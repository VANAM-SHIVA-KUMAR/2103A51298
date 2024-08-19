from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import requests

API_BASE_URL = 'http://20.244.56.144/test/companies/'
COMPANIES = ["AMZ", "FLP", "SNP", "MYN", "AZO"]

def fetch_products(company, category, top, min_price, max_price):
    url = f"{API_BASE_URL}{company}/categories/{category}/products?top={top}&minPrice={min_price}&maxPrice={max_price}"
    try:
        response = requests.get(url, timeout=1)
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, ValueError):
        return {"numbers": []}

def generate_unique_id(product):
    return f"{product['productName'].replace(' ', '_').lower()}_{product['price']}"

@require_http_methods(["GET"])
def top_products(request, categoryname):
    n = int(request.GET.get('n', 10))
    page = int(request.GET.get('page', 1))
    sort_by = request.GET.get('sort_by', 'rating')
    sort_order = request.GET.get('sort_order', 'desc')
    min_price = request.GET.get('minPrice', 0)
    max_price = request.GET.get('maxPrice', 100000)

    if n > 10:
        page_size = n
        start_index = (page - 1) * page_size
        end_index = page * page_size
    else:
        page_size = n
        start_index = 0
        end_index = n

    all_products = []
    for company in COMPANIES:
        product_data = fetch_products(company, categoryname, n, min_price, max_price)
        all_products.extend(product_data.get('numbers', []))

    seen = set()
    unique_products = []
    for product in all_products:
        prod_id = generate_unique_id(product)
        if prod_id not in seen:
            seen.add(prod_id)
            unique_products.append(product)

    sort_key = {
        'rating': 'rating',
        'price': 'price',
        'company': 'company',
        'discount': 'discount'
    }.get(sort_by, 'rating')

    unique_products.sort(key=lambda x: x[sort_key], reverse=(sort_order == 'desc'))

    paginated_products = unique_products[start_index:end_index]

    response_data = [
        {
            "id": generate_unique_id(product),
            "productName": product["productName"],
            "price": product["price"],
            "rating": product["rating"],
            "discount": product["discount"],
            "availability": product["availability"]
        }
        for product in paginated_products
    ]

    return JsonResponse({
        "products": response_data,
        "page": page,
        "pageSize": page_size,
        "totalProducts": len(unique_products),
        "totalPages": (len(unique_products) // page_size) + (1 if len(unique_products) % page_size else 0)
    })

@require_http_methods(["GET"])
def product_detail(request, categoryname, productid):
    all_products = []
    for company in COMPANIES:
        product_data = fetch_products(company, categoryname, 100, 0, 100000)
        all_products.extend(product_data.get('numbers', []))

    for product in all_products:
        if generate_unique_id(product) == productid:
            return JsonResponse({
                "id": productid,
                "productName": product["productName"],
                "price": product["price"],
                "rating": product["rating"],
                "discount": product["discount"],
                "availability": product["availability"]
            })

    return JsonResponse({"error": "Product not found"}, status=404)
