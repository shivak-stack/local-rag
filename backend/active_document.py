ACTIVE_DOCUMENT = None


def set_active_document(filename):
    global ACTIVE_DOCUMENT
    ACTIVE_DOCUMENT = filename


def get_active_document():
    return ACTIVE_DOCUMENT