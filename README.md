<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <title>Phần mềm bán hàng đơn giản</title>
  <style>
    body { font-family: Arial; padding: 20px; max-width: 800px; margin: auto; }
    input, button, select { margin: 5px; padding: 8px; }
    table { width: 100%; border-collapse: collapse; margin-top: 10px; }
    th, td { border: 1px solid #ccc; padding: 6px; text-align: left; }
    th { background: #f0f0f0; }
  </style>
</head>
<body>

<h2>📋 Phần mềm bán hàng mini</h2>

<h3>➕ Thêm sản phẩm</h3>
<input id="productName" placeholder="Tên sản phẩm">
<input id="productPrice" type="number" placeholder="Giá">
<button onclick="addProduct()">Thêm sản phẩm</button>

<h3>🛒 Chọn sản phẩm để bán</h3>
<select id="productSelect"></select>
<input id="quantity" type="number" value="1" min="1">
<button onclick="addOrder()">Bán</button>

<h3>🧾 Đơn hàng</h3>
<table id="orderTable">
  <thead>
    <tr><th>Sản phẩm</th><th>Số lượng</th><th>Giá</th><th>Thành tiền</th></tr>
  </thead>
  <tbody></tbody>
</table>

<h3>💰 Tổng tiền: <span id="totalAmount">0</span> VND</h3>

<script>
  let products = [];
  let orders = [];

  function addProduct() {
    const name = document.getElementById('productName').value;
    const price = parseFloat(document.getElementById('productPrice').value);
    if (!name || isNaN(price)) return alert("Vui lòng nhập tên và giá sản phẩm hợp lệ.");
    products.push({ name, price });
    updateProductSelect();
    document.getElementById('productName').value = '';
    document.getElementById('productPrice').value = '';
  }

  function updateProductSelect() {
    const select = document.getElementById('productSelect');
    select.innerHTML = '';
    products.forEach((p, index) => {
      const option = document.createElement('option');
      option.value = index;
      option.textContent = `${p.name} - ${p.price} VND`;
      select.appendChild(option);
    });
  }

  function addOrder() {
    const productIndex = document.getElementById('productSelect').value;
    const quantity = parseInt(document.getElementById('quantity').value);
    if (products[productIndex] && quantity > 0) {
      const product = products[productIndex];
      orders.push({ name: product.name, price: product.price, quantity });
      updateOrderTable();
    }
  }

  function updateOrderTable() {
    const tbody = document.querySelector("#orderTable tbody");
    tbody.innerHTML = '';
    let total = 0;
    orders.forEach(order => {
      const row = document.createElement('tr');
      const subtotal = order.price * order.quantity;
      total += subtotal;
      row.innerHTML = `<td>${order.name}</td><td>${order.quantity}</td><td>${order.price}</td><td>${subtotal}</td>`;
      tbody.appendChild(row);
    });
    document.getElementById("totalAmount").textContent = total.toLocaleString();
  }
</script>

</body>
</html>
