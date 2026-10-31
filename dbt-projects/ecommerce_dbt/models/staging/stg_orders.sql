select
    order_id,
    customer_id,
    product_id,
    quantity,
    unit_price,
    total_amount,
    order_date,
    order_status
from {{ source('staging', 'orders') }}