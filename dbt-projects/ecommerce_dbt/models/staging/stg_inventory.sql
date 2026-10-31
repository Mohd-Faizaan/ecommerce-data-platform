select
    product_id,
    snapshot_date,
    stock_quantity,
    warehouse_location
from {{ source('staging', 'inventory') }}