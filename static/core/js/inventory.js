function openEditModal(productId) {
    fetch(`/api/PHproduct/${productId}/`)
        .then(response => response.json())
        .then(data => {
            document.getElementById("productName").value = data.product_name;
            document.getElementById("productType").value = data.product_type;
            document.getElementById("supplierPrice").value = data.supplier_price;
            document.getElementById("price").value = data.price;
            document.getElementById("expirationDate").value = data.expiration_date;
            document.getElementById("stockLevel").value = data.stock_level;

            fetch(`/api/suppliers/list_for_pharmacy?pharmacy_id=${pharmacyId}`)
                .then(response => response.json())
                .then(suppliers => {
                    const supplierSelect = document.getElementById("supplier");
                    supplierSelect.innerHTML = '<option value="">Select Supplier</option>';
                    suppliers.forEach(supplier => {
                        const option = document.createElement('option');
                        option.value = supplier.id;
                        option.textContent = supplier.office;
                        supplierSelect.appendChild(option);
                    });

                    supplierSelect.value = data.supplier ? data.supplier.id : '';
                });

            document.getElementById("editForm").dataset.productId = productId;
            document.getElementById("editModal").style.display = "flex";
        })
        .catch(error => console.error("Error fetching product data:", error));
}

function submitEditForm() {
    const productId = document.getElementById("editForm").dataset.productId;
    const formData = new FormData(document.getElementById("editForm"));

    const dataToSend = {
        product: {
            name: document.getElementById("productName").value,
            product_type: formData.get('productType') || '', 
            id: productId 
        },
        supplier_price: formData.get('supplierPrice'),
        price: formData.get('price'),
        expiration_date: formData.get('expirationDate'),
        stock_level: formData.get('stockLevel'),
        supplier: formData.get('supplier') || null 
    };

    fetch(`/api/PHproduct/${productId}/`, {
        method: 'PUT',
        body: JSON.stringify(dataToSend),
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => {
        return response.json().then(data => ({ status: response.status, body: data }));
    })
    .then(({ status, body }) => {
        if (status === 200) {
            closeEditModal();
            alert("Product updated successfully");
            location.reload();
        } else {
            alert("Failed to update product: " + body.detail || "Unknown error");
        }
    })
    .catch(error => console.error('Error updating product:', error));
}

function openDeleteModal(productId) {
    document.getElementById("deleteForm").dataset.productId = productId;
    document.getElementById("deleteModal").style.display = "flex";
}

function submitDeleteForm() {
    const productId = document.getElementById("deleteForm").dataset.productId;

    fetch(`/api/PHproduct/${productId}/`, {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => {
        closeDeleteModal();
        alert("Product deleted successfully");
        location.reload();
    })
    .catch(error => console.error('Error deleting product:', error));
}

function closeEditModal() {
    document.getElementById("editModal").style.display = "none";
}

function closeDeleteModal() {
    document.getElementById("deleteModal").style.display = "none";
}

function fetchSuppliers(pharmacyId) {
    fetch(`/api/suppliers/list_for_pharmacy?pharmacy_id=${pharmacyId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            const supplierSelect = document.getElementById("supplier");
            supplierSelect.innerHTML = '<option value="">Select Supplier</option>';
            data.forEach(supplier => {
                const option = document.createElement("option");
                option.value = supplier.id;
                option.textContent = supplier.office;
                supplierSelect.appendChild(option);
            });
        })
        .catch(error => console.error("Error fetching suppliers:", error));
}

document.addEventListener("DOMContentLoaded", () => {
    fetchSuppliers(pharmacyId);
});
