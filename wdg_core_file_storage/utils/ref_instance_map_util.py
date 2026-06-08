from django.contrib.contenttypes.models import ContentType


def build_ref_instance_map(file_queryset):
    # Group by ref_type
    ref_map = {}
    for file in file_queryset:
        key = (file.ref_type, file.ref_id)
        if key not in ref_map:
            ref_map[key] = None  # Placeholder

    # Group by content type and resolve in bulk
    content_type_map = {}
    for ref_type, _ in ref_map.keys():
        content_type = ContentType.objects.get(model=ref_type.lower())
        if content_type.model_class() not in content_type_map:
            content_type_map[content_type.model_class()] = []

    for ref_type, ref_id in ref_map.keys():
        model = ContentType.objects.get(model=ref_type.lower()).model_class()
        content_type_map[model].append(ref_id)

    for model_class, ids in content_type_map.items():
        instances = model_class.objects.in_bulk(ids)
        for ref_id, instance in instances.items():
            ref_map[(model_class.__name__.lower(), str(ref_id))] = instance

    return ref_map
