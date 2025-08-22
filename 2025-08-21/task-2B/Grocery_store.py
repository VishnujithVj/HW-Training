# Grocery Store - Data Organizer

# 1. Inventory with grocery items
inventory = {
    "apple": 30.0,
    "banana": 20.0,
    "milk": 50.0,
    "bread": 40.0,
    "cheese": 80.0,
    "rice": 120.0,
    "eggs": 60.0
}

# 2. Show inventory to user
print("Welcome to the Grocery Store!")
print("Here is our inventory:")
for item, price in inventory.items():
    print(f"{item} - ₹{price}")
print()

# 3. User adds items to cart
cart = []
print("Enter items to add to your cart (type 'done' to finish):")
while True:
    product = input("Enter item: ").lower()
    if product == "done":
        break
    cart.append(product)

print("\nYour cart:", cart)
print("Type of cart:", type(cart))
print()

# 4. Calculate total bill with checking
total = 0
for item in cart:
    if item in inventory and inventory[item] is not None:
        total += inventory[item]
        print(f"{item} added to bill. Price: ₹{inventory[item]}")
    else:
        print(f"Warning: {item} is not available in inventory!")

print("\nTotal bill =", total)
print()

# 5. Unique items
unique_cart = set(cart)
print("Unique items in your cart:", unique_cart, "| Type:", type(unique_cart))
print()

# 6. Categories (just for demo)
categories = ("fruits", "dairy", "bakery", "staples")
print("Categories:", categories)
print("Type of categories:", type(categories))
print()

# 7. Add item with None price
inventory["chocolate"] = None
print("Chocolate price type:", type(inventory["chocolate"]))
print()

# 8. Apply discount if total > 100
is_discount_applied = False
if total > 100:
    is_discount_applied = True
    print("Discount applied! 🎉")
else:
    print("No discount applied.")

print("Final Bill =", total)
print("Is discount applied?", is_discount_applied)