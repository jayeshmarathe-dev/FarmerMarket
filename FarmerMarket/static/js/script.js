// Simple enhancements
document.addEventListener('DOMContentLoaded', function() {
    // Auto-dismiss alerts after 5s
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Confirm deletes
    const deleteLinks = document.querySelectorAll('a[href*="delete"]');
    deleteLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            if (!confirm('Are you sure?')) {
                e.preventDefault();
    }
    document.querySelectorAll('.order-form').forEach(f=>{
        const qty = f.querySelector('.order-qty');
        const totalEl = f.querySelector('.order-total-value');
        const unit = qty ? parseFloat(qty.dataset.unitPrice || '0') : 0;
        const update = ()=>{
            const q = qty ? parseInt(qty.value || '1', 10) : 1;
            const total = (unit * q).toFixed(2);
            if(totalEl){ totalEl.textContent = total; }
            const addForm = f.closest('.card-body')?.querySelector('.add-cart-form');
            const hiddenQty = addForm?.querySelector('.add-cart-qty');
            if(hiddenQty){ hiddenQty.value = q; }
        };
        if(qty){
            update();
            qty.addEventListener('input', update);
            qty.addEventListener('change', update);
        }
    });
    const cartForm = document.getElementById('cartCheckoutForm');
    if(cartForm && navigator.geolocation){
        navigator.geolocation.getCurrentPosition(function(pos){
            cartForm.querySelector('input[name="lat"]').value = pos.coords.latitude;
            cartForm.querySelector('input[name="lng"]').value = pos.coords.longitude;
        });
    }
    const cartQtyInputs = document.querySelectorAll('.cart-qty');
    if(cartQtyInputs.length){
        const grandEl = document.getElementById('cart-grand-total');
        const recalc = ()=>{
            let grand = 0;
            document.querySelectorAll('tr').forEach(row=>{
                const qty = row.querySelector('.cart-qty');
                const unit = qty ? parseFloat(qty.dataset.unitPrice || '0') : 0;
                const q = qty ? parseInt(qty.value || '1', 10) : 1;
                const line = unit * q;
                const lt = row.querySelector('.line-total');
                if(lt){ lt.textContent = '₹' + line.toFixed(2); }
                grand += line;
            });
            if(grandEl){ grandEl.textContent = grand.toFixed(2); }
        };
        cartQtyInputs.forEach(i=>{
            i.addEventListener('input', recalc);
            i.addEventListener('change', recalc);
        });
        recalc();
    }
});
    });

    // Geolocation for order forms
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(function(pos){
            const lat = pos.coords.latitude;
            const lng = pos.coords.longitude;
            document.querySelectorAll('form[action*="/order/"]').forEach(f => {
                let latInput = f.querySelector('input[name="lat"]');
                let lngInput = f.querySelector('input[name="lng"]');
                if(!latInput){ latInput = document.createElement('input'); latInput.type='hidden'; latInput.name='lat'; f.prepend(latInput); }
                if(!lngInput){ lngInput = document.createElement('input'); lngInput.type='hidden'; lngInput.name='lng'; f.prepend(lngInput); }
                latInput.value = lat;
                lngInput.value = lng;
            });
        }, function(err){
            console.warn('Geolocation unavailable:', err);
        }, {enableHighAccuracy:true, timeout:10000});
    }
    document.querySelectorAll('.order-form').forEach(f=>{
        const qty = f.querySelector('.order-qty');
        const totalEl = f.querySelector('.order-total-value');
        const unit = qty ? parseFloat(qty.dataset.unitPrice || '0') : 0;
        const update = ()=>{
            const q = qty ? parseInt(qty.value || '1', 10) : 1;
            const total = (unit * q).toFixed(2);
            if(totalEl){ totalEl.textContent = total; }
        };
        if(qty){
            update();
            qty.addEventListener('input', update);
            qty.addEventListener('change', update);
        }
    });
});
