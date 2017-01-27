from . import popolo_extra as models


def check_paired_models():
    errors = []
    for base, extra in (
        (models.Person, models.PersonExtra),
        (models.Organization, models.OrganizationExtra),
        (models.Post, models.PostExtra),
        (models.Area, models.AreaExtra),
        (models.Image, models.ImageExtra),
    ):
        format_kwargs = {'base': base.__name__, 'extra': extra.__name__}
        base_ids = set(
            base.objects.values_list('pk', flat=True))
        base_ids_from_extra = set(
            extra.objects.values_list('base_id', flat=True))
        extra_ids = set(
            extra.objects.values_list('pk', flat=True))
        if len(base_ids) != len(extra_ids):
            msg = 'There were {base_count} {base} objects, but ' \
                  '{extra_count} {extra} objects'
            fmt = format_kwargs.copy()
            fmt.update({
                'base_count': len(base_ids),
                'extra_count': len(extra_ids)})
            errors.append(msg.format(**fmt))
        base_ids_with_no_extra = sorted(base_ids - base_ids_from_extra)
        for base_id in base_ids_with_no_extra:
            msg = 'The {base} object with ID {id} had no corresponding ' \
                  '{extra} object'
            fmt = format_kwargs.copy()
            fmt.update({'id': base_id})
            errors.append(msg.format(**fmt))
        # We could try to check for other errors here, but they are
        # prevented by various constraints. For example, you can't
        # have an *Extra object with no corresponding base object,
        # because the OneToOneField 'base' fields have the default
        # null=False. As a second example, you can't have more than
        # one *Extra object pointing to the same base object because
        # there is a unique constraint on the base_id field.
    return errors
