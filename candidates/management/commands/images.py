import hashlib

def get_file_md5sum(filename):
    with open(filename, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

def image_uploaded_already(api_collection, object_id, image_filename):
    person_data = api_collection(object_id).get()['result']
    md5sum = get_file_md5sum(image_filename)
    for image in person_data.get('images', []):
        if image.get('notes') == 'md5sum:' + md5sum:
            return True
    return False
