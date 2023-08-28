from sqlalchemy import func
from sqlalchemy import orm


class BaseQuery(orm.Query):
    """SQLAlchemy :class:`~sqlalchemy.orm.query.Query` subclass with convenience methods for querying in a web application.

    This is the default :attr:`~Model.query` object used for models, and exposed as :attr:`~SQLAlchemy.Query`.
    Override the query class for an individual model by subclassing this and setting :attr:`~Model.query_class`.
    """

    def order_by_text(self, order_by):
        model_cls = self.column_descriptions[0].get("type")
        if not order_by:
            return self.order_by(model_cls.id.desc())

        if not isinstance(order_by, list):
            order_by = [order_by]
        order_items = []
        for order_kw in order_by:
            desc = order_kw.startswith("-")
            order_kw = order_kw.strip("-")

            if order_kw in model_cls.__table__.columns:
                order_item = getattr(model_cls, order_kw)
                if desc:
                    order_item = order_item.desc()
                order_items.append(order_item)

        if order_items:
            query = self.order_by(*order_items)
        else:
            query = self.order_by(model_cls.id.desc())
        return query

    def paginate(self, page=1, page_size=10):
        page = max(page, 1)
        query = self.offset((page - 1) * page_size).limit(page_size)
        return query

    def to_dict_list(self, exclude_fields=None, extra_fields=None):
        all_data = self.all()
        data_list = []
        for content in all_data:
            content_dict = content.to_dict(
                exclude_fields=exclude_fields, extra_fields=extra_fields
            )
            data_list.append(content_dict)

        return data_list

    def get_total(self):
        model_cls = self.column_descriptions[0].get("type")
        total = self.with_entities(func.count(model_cls.id)).scalar()
        return total
