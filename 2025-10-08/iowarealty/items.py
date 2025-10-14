from mongoengine import Document, StringField, ListField, DictField

class AgentItem(Document):
    profile_url = StringField(required=True, unique=True)
    first_name = StringField()
    middle_name = StringField()
    last_name = StringField()
    image_url = StringField()
    office_name = StringField()
    address = StringField()
    description = StringField()
    languages = ListField(StringField())
    social = DictField()
    website = StringField()
    email = StringField()
    title = StringField()
    country = StringField()
    city = StringField()
    zipcode = StringField()
    state = StringField()
    agent_phone_numbers = ListField(StringField())
    office_phone_numbers = ListField(StringField())

    meta = {"collection": "iowarealty_data"}
