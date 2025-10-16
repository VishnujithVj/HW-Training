import json
import time
import logging
import re
import requests
from lxml import html
from datetime import datetime, timezone
from items import ProductData, ProductURL
from settings import HEADERS

logging.basicConfig(
    filename="bipa_parser.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

class BipaProductParser:
    def __init__(self):
        self.session = requests.Session()

    def clean_text(self, text):
        return " ".join(text.split()) if text else ""

    def extract_label_value_pairs(self, tree):
        """
        Extract simple label:value pairs from several HTML patterns:
        - <dl><dt><dd>
        - block text with colon 'Label : value' (p/div/li)
        """
        pairs = []

        dts = tree.xpath('//dl/dt')
        dds = tree.xpath('//dl/dd')
        for dt, dd in zip(dts, dds):
            label = self.clean_text(dt.text_content())
            value = self.clean_text(dd.text_content())
            if label and value:
                pairs.append((label, value))

    
        nodes = tree.xpath('//div | //p | //li')
        for node in nodes:
            text = self.clean_text(node.text_content())
        
            if ":" in text and len(text.split(":")) <= 6:
                label, value = text.split(":", 1)
                label = label.strip()
                value = value.strip()
                if label and value:
                    pairs.append((label, value))
        return pairs

    def _safe_set(self, data_obj, field_name, value):
        """Set attribute only if it's defined on the Document (avoid unknown fields)."""
        if not field_name:
            return
    
        if hasattr(data_obj, "_fields") and field_name in data_obj._fields:
            setattr(data_obj, field_name, value)

    def _normalize_grammage(self, data_obj, raw_value):
        """Extract numeric and unit and normalize to base units (ml/g)."""
        if not raw_value:
            return
        v = raw_value.strip().lower().replace(",", ".")
        
        m = re.search(r'([\d\.]+)\s*(ml|l|g|kg)\b', v, re.I)
        if not m:
        
            m = re.search(r'([\d\.]+)(ml|l|g|kg)\b', v, re.I)
        if not m:
            return

        qty_raw = m.group(1)
        unit_raw = m.group(2).lower()
        try:
            q = float(qty_raw)
        except Exception:
        
            self._safe_set(data_obj, "grammage_quantity", qty_raw)
            self._safe_set(data_obj, "grammage_unit", unit_raw)
            return

        if unit_raw == "l":
            q *= 1000.0
            unit_norm = "ml"
        elif unit_raw == "kg":
            q *= 1000.0
            unit_norm = "g"
        else:
            unit_norm = unit_raw

        if abs(q - int(q)) < 1e-9:
            qty_str = str(int(q))
        else:
            qty_str = ("%g" % q)  

        self._safe_set(data_obj, "grammage_quantity", qty_str)
        self._safe_set(data_obj, "grammage_unit", unit_norm)

    def parse_product(self, url):
        url = url.rstrip("/")
        unique_id = url.split("/")[-1]
        if not unique_id:
            logging.warning(f"Empty unique_id for URL: {url}")
            return None

        try:
            r = self.session.get(url, headers=HEADERS, timeout=25)
            r.raise_for_status()
            tree = html.fromstring(r.text)
        except Exception as e:
            logging.error(f"Failed to fetch {url}: {e}")
            return None

        data = ProductData()
        self._safe_set(data, "unique_id", unique_id)
        self._safe_set(data, "pdp_url", url)
        self._safe_set(data, "competitor_name", "BIPA")
        self._safe_set(data, "store_name", "BIPA Online")
        self._safe_set(data, "extraction_date", datetime.now(timezone.utc))

        product_json = None
        for script in tree.xpath('//script[@type="application/ld+json"]/text()'):
            try:
                j = json.loads(script)
            except Exception:
                continue
            if isinstance(j, dict):
                if "mainEntity" in j and isinstance(j["mainEntity"], dict):
                    product_json = j["mainEntity"]
                    break
                
                if j.get("@type") == "Product" or j.get("mainEntityOfPage") or j.get("name") and j.get("offers"):
                    product_json = j
                    break
        
            if isinstance(j, list):
                for item in j:
                    if isinstance(item, dict) and (item.get("@type") == "Product" or "offers" in item):
                        product_json = item
                        break
                if product_json:
                    break

        if product_json:
            self._safe_set(data, "product_name", product_json.get("name", "") or "")
        
            brand_val = ""
            try:
                b = product_json.get("brand", "")
                if isinstance(b, dict):
                    brand_val = b.get("name", "") or ""
                elif isinstance(b, str):
                    brand_val = b
            except Exception:
                brand_val = ""
            self._safe_set(data, "brand", brand_val)
            offers = product_json.get("offers", {}) or {}
            price = offers.get("price") or product_json.get("price")
            if price is not None:
                self._safe_set(data, "selling_price", str(price))
            self._safe_set(data, "currency", offers.get("priceCurrency", "") or "")
        
            barcode = product_json.get("gtin13") or product_json.get("gtin14") or product_json.get("gtin8") or product_json.get("mpn", "")
            self._safe_set(data, "barcode", barcode)
            self._safe_set(data, "competitor_product_key", product_json.get("sku", "") or "")
        
            desc = product_json.get("description", "") or ""
            try:
                desc_tree = html.fromstring(desc)
                desc_text = self.clean_text(desc_tree.text_content())
            except Exception:
                desc_text = self.clean_text(desc)
            self._safe_set(data, "product_description", desc_text)

            agg = product_json.get("aggregateRating", {}) or {}
            self._safe_set(data, "rating", str(agg.get("ratingValue", "") or ""))
            self._safe_set(data, "review", str(agg.get("reviewCount", "") or ""))
        
            images = product_json.get("image", []) or []
            if isinstance(images, list):
                for i in range(min(3, len(images))):
                    self._safe_set(data, f"image_url_{i+1}", images[i])
            elif isinstance(images, str):
                self._safe_set(data, "image_url_1", images)

        if not getattr(data, "product_description", ""):
            meta_desc = tree.xpath('//meta[@name="description"]/@content')
            if meta_desc:
                self._safe_set(data, "product_description", self.clean_text(meta_desc[0]))

        """ Extract breadcrumb and hierarchy levels """
        bc_script = tree.xpath('//script[contains(text(),"BreadcrumbList")]/text()')
        if bc_script:
            try:
                bc_json = json.loads(bc_script[0])
                items = bc_json.get("itemListElement", []) or []
                names = [it.get("name", "") for it in items if isinstance(it, dict)]
                if names:
                    self._safe_set(data, "producthierarchy_level1", names[0] if len(names) > 0 else "")
                    self._safe_set(data, "producthierarchy_level2", names[1] if len(names) > 1 else "")
                    self._safe_set(data, "producthierarchy_level3", names[2] if len(names) > 2 else "")
                    self._safe_set(data, "breadcrumb", " > ".join([n for n in names if n]))
            except Exception:
                pass


        info_pairs = self.extract_label_value_pairs(tree)

        for tr in tree.xpath('//table//tr'):
        
            cells = [self.clean_text(" ".join(tr.xpath('.//th//text() | .//td//text()')))]
            if cells and ":" in cells[0]:
                label, value = cells[0].split(":", 1)
                info_pairs.append((label.strip(), value.strip()))

        
        for label, value in info_pairs:
            l = label.lower()
            val = value.strip()
            if not val:
                continue
            if "ingredient" in l or l.strip() in ("ingredients", "zutaten", "zutaten:"):
                self._safe_set(data, "ingredients", val)

            elif "label" in l or "kennzeichnung" in l or "contains" in l:
                self._safe_set(data, "labelling", val)

            elif "direction" in l or "gebrauch" in l or "anwendung" in l:
                self._safe_set(data, "instructionforuse", val)

            elif "country of origin" in l or "countries of origin" in l or "herkunft" in l or "herkunftsländer" in l:
                self._safe_set(data, "country_of_origin", val)

            elif "storage" in l or "lager" in l or "aufbewahrung" in l:
                self._safe_set(data, "storage_instructions", val)

            elif "warning" in l or "hinweis" in l or "labeling" in l:
        
                self._safe_set(data, "Warning", val)

            elif "allergen" in l or "allergens" in l or "contains" in l:
                self._safe_set(data, "allergens", val)

            elif "gross weight" in l or "bruttogewicht" in l or "bruttogew." in l:
                self._safe_set(data, "netweight", val)
            
                self._normalize_grammage(data, val)

            elif any(k in l for k in ["net content", "net quantity", "nettogehalt", "nettogeh.", "nettogehalt"]):
                self._safe_set(data, "netcontent", val)
                self._normalize_grammage(data, val)

            elif any(k in l for k in ["net weight", "gewicht", "nutzinhalt"]):
                self._safe_set(data, "netweight", val)
                self._normalize_grammage(data, val)

            elif "diet" in l or "vegan" in l or "vegetarian" in l:
                self._safe_set(data, "dietary_lifestyle", val)

            elif "address" in l or "adresse" in l:
            
                if "manufacturer" in l or "hersteller" in l:
                    self._safe_set(data, "manufacturer_address", val)
                elif "importer" in l or "importeur" in l:
                    self._safe_set(data, "importer_address", val)
                else:
                
                    self._safe_set(data, "distributor_address", val)

            elif "name" in l and "distributor" in l or "vertrieb" in l:
                self._safe_set(data, "distributor_address", val)

            elif "packaging" in l or "verpackung" in l:
                self._safe_set(data, "packaging", "")

            elif "recycling" in l or "recycle" in l or "ara" in l:
                self._safe_set(data, "recycling_information", val)

            elif "region" in l:
                self._safe_set(data, "region", val)

            elif "grade" in l:
                self._safe_set(data, "grade", val)
    
            elif l.strip() in ("upc", "ean", "gtin"):
                self._safe_set(data, "upc", val)

        for node in tree.xpath('//p | //span | //li'):
            txt = self.clean_text(node.text_content())
            if not txt or len(txt) > 40:
                continue
        
            if re.search(r'^[\d\.,]+\s*(ml|l|g|kg)\b', txt, re.I):
                self._normalize_grammage(data, txt)
            
                if not getattr(data, "netcontent", ""):
                    self._safe_set(data, "netcontent", txt)
                break

        html_images = tree.xpath('//div[@data-fancybox="gallery"]/@href | //div[contains(@class,"product-gallery")]//img/@src | //img[contains(@class,"product")]/@src')
        for i, img in enumerate(html_images[:3]):
            self._safe_set(data, f"image_url_{i+1}", img)

        for field in data._fields:
            if getattr(data, field, None) is None:
            
                if field == "instock":
        
                    try:
                        setattr(data, "instock", True)
                    except Exception:
                        setattr(data, "instock", "")
                else:
                    setattr(data, field, "")

        return data

    def parse_all(self, limit=None):
        urls = ProductURL.objects()
        if limit:
            urls = urls[:limit]

        for u in urls:
            product_url = getattr(u, "product_url", "").rstrip("/")
            if not product_url:
                continue
            unique_id = product_url.split("/")[-1]
            if not unique_id:
                logging.warning(f"Skipping URL with empty unique_id: {product_url}")
                continue
            if ProductData.objects(unique_id=unique_id).first():
                continue

            print(f" Parsing: {product_url}")
            data = self.parse_product(product_url)
            if data:
                try:
                    """ ensure we didn't accidentally create invalid string id fields."""
                    if hasattr(data, "id"):
                        try:
                            delattr(data, "id")
                        except Exception:
                            pass
                    if hasattr(data, "_id") and isinstance(getattr(data, "_id"), str):
                        try:
                            delattr(data, "_id")
                        except Exception:
                            pass

                    data.save()
                    logging.info(f"Saved: {product_url}")
                except Exception as e:
                    print(f"Save failed {product_url}: {e}")
                    logging.error(f"Save failed {product_url}: {e}")
            time.sleep(1)


if __name__ == "__main__":
    BipaProductParser().parse_all(limit=500)
