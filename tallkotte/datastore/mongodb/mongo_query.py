from typing import Any, Optional, NotRequired, TypedDict


class MongoQuery(TypedDict):
    filter: dict[str, Any]
    projection: NotRequired[dict[str, Any]]
    sort: NotRequired[dict[str, Any]]
    limit: NotRequired[int]


class MongoQueryBuilder:
    def __init__(self, **initial_query: Any):
        self.query = initial_query

    def and_(self, **condition: Any) -> 'MongoQueryBuilder':
        self.query.setdefault('$and', []).append(condition)
        return self

    def or_(self, **condition: Any) -> 'MongoQueryBuilder':
        self.query.setdefault('$or', []).append(condition)
        return self

    def build(self) -> MongoQuery:
        return MongoQuery(filter=self.query)


def mongo_query(filter: dict[str, Any],
                projection: Optional[dict[str, str]] = None,
                sort: Optional[dict[str, str]] = None,
                limit: Optional[int] = None) -> MongoQuery:
    fields: dict[str, dict[str, Any] | int] = {'filter': filter}
    if projection:
        fields['projection'] = projection
    if sort:
        fields['sort'] = sort
    if limit:
        fields['limit'] = limit
    return MongoQuery(**fields)
