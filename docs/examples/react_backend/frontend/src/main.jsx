import { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

const API_URL = "http://127.0.0.1:8000/api/products";

function App() {
  const [products, setProducts] = useState([]);
  const [name, setName] = useState("");
  const [price, setPrice] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  async function loadProducts() {
    setIsLoading(true);
    setError("");
    try {
      const response = await fetch(API_URL);
      if (!response.ok) throw new Error("Could not load products.");
      const data = await response.json();
      setProducts(data.products);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    loadProducts();
  }, []);

  async function createProduct(event) {
    event.preventDefault();
    setError("");
    try {
      const response = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, price: Number(price) }),
      });
      if (!response.ok) throw new Error("Could not create the product.");
      const data = await response.json();
      setProducts((current) => [...current, data.product]);
      setName("");
      setPrice("");
    } catch (requestError) {
      setError(requestError.message);
    }
  }

  async function deleteProduct(productId) {
    setError("");
    try {
      const response = await fetch(`${API_URL}/${productId}`, { method: "DELETE" });
      if (!response.ok) throw new Error("Could not delete the product.");
      setProducts((current) => current.filter((product) => product.id !== productId));
    } catch (requestError) {
      setError(requestError.message);
    }
  }

  return (
    <main>
      <header>
        <p className="eyebrow">Flaxon + React</p>
        <h1>Products</h1>
        <p>A small frontend that talks to the accompanying Flaxon API.</p>
      </header>

      <form onSubmit={createProduct}>
        <label>
          Product name
          <input value={name} onChange={(event) => setName(event.target.value)} required />
        </label>
        <label>
          Price
          <input type="number" min="0" step="0.01" value={price} onChange={(event) => setPrice(event.target.value)} required />
        </label>
        <button type="submit">Add product</button>
      </form>

      {error && <p className="error">{error}</p>}
      {isLoading ? <p>Loading products…</p> : (
        <ul>
          {products.map((product) => (
            <li key={product.id}>
              <span>{product.name}</span>
              <strong>${product.price.toFixed(2)}</strong>
              <button type="button" className="secondary" onClick={() => deleteProduct(product.id)}>
                Delete
              </button>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}

createRoot(document.getElementById("root")).render(<App />);
