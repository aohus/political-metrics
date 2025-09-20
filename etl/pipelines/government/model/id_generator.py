import uuid


def generate_unique_id():
    """유니크 ID 생성"""
    return str(uuid.uuid4())


def generate_short_id():
    """짧은 ID 생성 (하이픈 제거)"""
    return uuid.uuid4().hex


class model_meta(type):
    def __call__(cls, *args, **kwargs):
        # Create the instance
        instance = super().__call__(*args, **kwargs)
        # Auto-generate id if not provided
        if not hasattr(instance, 'id') or getattr(instance, 'id', None) is None:
            instance.id = generate_short_id()
        return instance
