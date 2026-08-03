
# React Backend Example

This example demonstrates a Flaxon backend API designed for a React frontend application.

Features:

- CORS configuration
- REST API endpoints
- Request validation
- CRUD operations
- Filtering
- Statistics endpoint

---

# Application Code

## app.py

```python
from flaxon import Flaxon
from flaxon.middleware import CORSMiddleware
from flaxon.validation import Schema, fields


app = Flaxon(
    "react-backend",
    debug=True,
)


# Allow React development servers
app.add_middleware(
    CORSMiddleware,
    allowed_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
)


# Product Schema

class CreateProduct(Schema):

    name = fields.String(
        required=True,
        min_length=2,
        max_length=100,
    )

    price = fields.FloatField(
        required=True,
        minimum=0,
    )

    description = fields.String(
        required=False,
        max_length=500,
    )

    category = fields.String(
        required=False,
        max_length=50,
    )

    in_stock = fields.BoolField(
        default=True,
    )


# Storage

products = [
    {
        "id": 1,
        "name": "Laptop",
        "price": 999.99,
        "description": "Developer laptop",
        "category": "electronics",
        "in_stock": True,
    },
    {
        "id": 2,
        "name": "Keyboard",
        "price": 79.99,
        "description": "Mechanical keyboard",
        "category": "accessories",
        "in_stock": True,
    },
]


product_id_counter = 3


# Routes


@app.get("/api/products")
async def list_products(request):

    category = request.query.get(
        "category"
    )

    in_stock = request.query.get_bool(
        "in_stock"
    )


    result = products


    if category:
        result = [
            p for p in result
            if p["category"] == category
        ]


    if in_stock is not None:
        result = [
            p for p in result
            if p["in_stock"] == in_stock
        ]


    return {
        "data": result,
        "total": len(result),
    }



@app.get("/api/products/<int:product_id>")
async def get_product(product_id: int):

    for product in products:

        if product["id"] == product_id:
            return product


    return {
        "error": "Product not found"
    }, 404



@app.post("/api/products")
async def create_product(
    data: CreateProduct
):

    global product_id_counter


    product = data.to_dict()

    product["id"] = product_id_counter

    product_id_counter += 1


    products.append(product)


    return {
        "created": True,
        "product": product,
    }, 201



@app.put("/api/products/<int:product_id>")
async def update_product(
    product_id: int,
    data: CreateProduct,
):

    for product in products:

        if product["id"] == product_id:

            product.update(
                data.to_dict()
            )

            return {
                "updated": True,
                "product": product,
            }


    return {
        "error": "Product not found"
    }, 404



@app.delete("/api/products/<int:product_id>")
async def delete_product(
    product_id: int
):

    for index, product in enumerate(products):

        if product["id"] == product_id:

            products.pop(index)

            return {
                "deleted": True,
            }


    return {
        "error": "Product not found"
    }, 404



@app.get("/api/categories")
async def list_categories():

    categories = list(
        set(
            p["category"]
            for p in products
            if p.get("category")
        )
    )


    return {
        "categories": categories
    }



@app.get("/api/stats")
async def get_stats():

    total = len(products)

    in_stock = sum(
        1
        for p in products
        if p["in_stock"]
    )


    total_value = sum(
        p["price"]
        for p in products
    )


    return {
        "total_products": total,
        "in_stock": in_stock,
        "out_of_stock": total - in_stock,
        "total_value": round(
            total_value,
            2,
        ),
    }
````

---

# Running the Application

Install dependencies:

```bash
pip install flaxon[standard]
```

Run:

```bash
flaxon run app:app --reload --host 0.0.0.0 --port 8000
```

---

# React Client Example

## api.js

```javascript
const API_URL = "http://localhost:8000/api";


export async function getProducts() {

    const response = await fetch(
        `${API_URL}/products`
    );

    return response.json();
}



export async function getProduct(id) {

    const response = await fetch(
        `${API_URL}/products/${id}`
    );

    return response.json();
}



export async function createProduct(product) {

    const response = await fetch(
        `${API_URL}/products`,
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(product),
        }
    );


    return response.json();
}



export async function updateProduct(
    id,
    product
){

    const response = await fetch(
        `${API_URL}/products/${id}`,
        {
            method: "PUT",
            headers:{
                "Content-Type":"application/json",
            },
            body: JSON.stringify(product),
        }
    );


    return response.json();
}



export async function deleteProduct(id){

    const response = await fetch(
        `${API_URL}/products/${id}`,
        {
            method:"DELETE",
        }
    );


    return response.json();
}
```

---

# React Component Example

## App.jsx

```jsx
import {
    useEffect,
    useState
} from "react";

import {
    getProducts,
    deleteProduct
} from "./api";


export default function App(){

    const [
        products,
        setProducts
    ] = useState([]);


    useEffect(()=>{

        loadProducts();

    },[]);



    async function loadProducts(){

        const data = await getProducts();

        setProducts(
            data.data
        );
    }



    async function removeProduct(id){

        await deleteProduct(id);

        loadProducts();
    }



    return (

        <div>

            <h1>
                Products
            </h1>


            {
                products.map(product => (

                    <div key={product.id}>

                        <h3>
                            {product.name}
                        </h3>


                        <p>
                            ${product.price}
                        </p>


                        <button
                            onClick={() =>
                                removeProduct(
                                    product.id
                                )
                            }
                        >
                            Delete
                        </button>

                    </div>

                ))
            }


        </div>

    );
}
```

---

# API Endpoints

| Method | Endpoint            | Description        |
| ------ | ------------------- | ------------------ |
| GET    | `/api/products`     | List products      |
| GET    | `/api/products/:id` | Get product        |
| POST   | `/api/products`     | Create product     |
| PUT    | `/api/products/:id` | Update product     |
| DELETE | `/api/products/:id` | Delete product     |
| GET    | `/api/categories`   | Product categories |
| GET    | `/api/stats`        | Product statistics |

---

# Testing

Get products:

```bash
curl http://localhost:8000/api/products
```

Create product:

```bash
curl -X POST http://localhost:8000/api/products \
-H "Content-Type: application/json" \
-d '{"name":"Monitor","price":200}'
```

Delete product:

```bash
curl -X DELETE http://localhost:8000/api/products/1
```

---

## Production Improvements

For production React applications:

* Replace memory storage with PostgreSQL
* Add JWT authentication
* Add pagination
* Add file uploads
* Add WebSocket support
* Add rate limiting
* Deploy frontend and backend separately

