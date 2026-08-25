from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Product
from app.schemas import ProductCreate, ProductUpdate


def get_product_by_id(
    database: Session,
    product_id: UUID,
) -> Product | None:
    return database.get(Product, product_id)


def get_product_by_sku(
    database: Session,
    sku: str,
) -> Product | None:
    statement = select(Product).where(Product.sku == sku)
    return database.scalar(statement)


def create_product(
    database: Session,
    product_data: ProductCreate,
) -> Product:
    product = Product(**product_data.model_dump())

    database.add(product)
    database.commit()
    database.refresh(product)

    return product


def list_products(
    database: Session,
    offset: int = 0,
    limit: int = 100,
) -> list[Product]:
    statement = (
        select(Product)
        .order_by(Product.created_at.desc())
        .offset(offset)
        .limit(limit)
    )

    return list(database.scalars(statement).all())


def update_product(
    database: Session,
    product: Product,
    product_data: ProductUpdate,
) -> Product:
    update_data = product_data.model_dump(exclude_unset=True)

    for field_name, field_value in update_data.items():
        setattr(product, field_name, field_value)

    database.commit()
    database.refresh(product)

    return product


def delete_product(
    database: Session,
    product: Product,
) -> None:
    database.delete(product)
    database.commit()