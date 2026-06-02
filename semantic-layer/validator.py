from models import TABLE_SCHEMA


def validate_field(field: str):
    for table in TABLE_SCHEMA.values():
        if field in table["fields"]:
            return True
    return False


def validate_filter(filter_item):
    return validate_field(filter_item["field"])
