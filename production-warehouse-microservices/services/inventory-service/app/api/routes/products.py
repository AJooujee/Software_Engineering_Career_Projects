from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Response,
    status,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models import Product
from app.repositories.product import (
    create_product,
    delete_product,
    get_product_by_id,
    get_product_by_sku,
    list_products,
    update_product,
)
from app.schemas import ProductCreate, ProductResponse, ProductUpdate


router = APIRouter(
    prefix="/products",
    tags=["Products"],
)


def get_product_or_404(
    product_id: UUID,
    database: Session,
) -> Product:
    product = get_product_by_id(database, product_id)

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product '{product_id}' was not found",
        )

    return product


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_product_endpoint(
    product_data: ProductCreate,
    database: Session = Depends(get_db),
) -> Product:
    existing_product = get_product_by_sku(database, product_data.sku)

    if existing_product is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Product with SKU '{product_data.sku}' already exists",
        )

    try:
        return create_product(database, product_data)
    except IntegrityError as error:
        database.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Product with SKU '{product_data.sku}' already exists",
        ) from error


@router.get(
    "",
    response_model=list[ProductResponse],
)
def list_products_endpoint(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    database: Session = Depends(get_db),
) -> list[Product]:
    return list_products(database, offset=offset, limit=limit)


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
)
def get_product_endpoint(
    product_id: UUID,
    database: Session = Depends(get_db),
) -> Product:
    return get_product_or_404(product_id, database)


@router.patch(
    "/{product_id}",
    response_model=ProductResponse,
)
def update_product_endpoint(
    product_id: UUID,
    product_data: ProductUpdate,
    database: Session = Depends(get_db),
) -> Product:
    product = get_product_or_404(product_id, database)
    return update_product(database, product, product_data)


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_product_endpoint(
    product_id: UUID,
    database: Session = Depends(get_db),
) -> Response:
    product = get_product_or_404(product_id, database)
    delete_product(database, product)

    return Response(status_code=status.HTTP_204_NO_CONTENT)