class QueryMeta(type):
    def __getitem__(self, item):
        return object


class Query(metaclass=QueryMeta):
    pass
