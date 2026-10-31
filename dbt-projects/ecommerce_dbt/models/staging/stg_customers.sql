select
    customer_id,
    name as customer_name,
    email,
    signup_date,
    city,
    state
from {{ source('staging', 'customers') }}