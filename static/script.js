document.getElementById('transactionForm').addEventListener('submit', async function(e) {
    e.preventDefault();

    const submitBtn = document.getElementById('submitBtn');
    const loading = document.getElementById('loading');
    const alert = document.getElementById('alert');

    // Hide previous results
    document.getElementById('resultContainer').style.display = 'none';
    document.getElementById('otpSection').style.display = 'none';
    alert.style.display = 'none';

    // Show loading
    submitBtn.disabled = true;
    loading.style.display = 'block';

    const formData = {
        sender_id: document.getElementById('sender_id').value,
        receiver_id: document.getElementById('receiver_id').value,
        amount: parseFloat(document.getElementById('amount').value),
        password: document.getElementById('password').value
    };

    try {
        const response = await fetch('/predict', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });

        const result = await response.json();

        loading.style.display = 'none';
        submitBtn.disabled = false;

        if (response.ok) {
            displayResult(result);
        } else {
            showAlert('error', result.error || 'An error occurred');
        }

    } catch (error) {
        loading.style.display = 'none';
        submitBtn.disabled = false;
        showAlert('error', 'Network error. Please try again.');
    }
});

document.getElementById('verifyBtn').addEventListener('click', async function() {
    const otpInput = document.getElementById('verifyOtp').value;

    if (!otpInput) {
        showAlert('error', 'Please enter the OTP sent to your email');
        return;
    }

    try {
        const response = await fetch('/verify_otp', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                sender_id: document.getElementById('sender_id').value,
                otp: otpInput
            })
        });

        const result = await response.json();

        if (result.verified) {
            showAlert('success', result.message);
            document.getElementById('otpSection').style.display = 'none';
            document.getElementById('resultContainer').style.display = 'block';
            document.getElementById('resultContainer').className = 'result-container result-normal';
            document.getElementById('resultTitle').style.color = '#155724';
            document.getElementById('resultIcon').className = 'fas fa-check-circle';
            document.getElementById('resultText').textContent = 'Transaction Successful';
            document.getElementById('resultDetails').innerHTML = `
                <div class="detail-item"><div class="detail-label">Sender ID</div><div class="detail-value">${result.sender_id}</div></div>
                <div class="detail-item"><div class="detail-label">Receiver ID</div><div class="detail-value">${result.receiver_id}</div></div>
                <div class="detail-item"><div class="detail-label">Amount</div><div class="detail-value">$${result.amount.toFixed(2)}</div></div>
                <div class="detail-item"><div class="detail-label">New Sender Balance</div><div class="detail-value">$${result.newbalanceOrig.toFixed(2)}</div></div>
                <div class="detail-item"><div class="detail-label">New Receiver Balance</div><div class="detail-value">$${result.newbalanceDest.toFixed(2)}</div></div>
            `;
            document.getElementById('submitBtn').disabled = false;
            document.getElementById('transactionForm').reset();
        } else {
            showAlert('error', result.message);
        }

    } catch (error) {
        showAlert('error', 'Verification failed. Please try again.');
    }
});

function displayResult(result) {
    const container = document.getElementById('resultContainer');
    const title = document.getElementById('resultTitle');
    const icon = document.getElementById('resultIcon');
    const text = document.getElementById('resultText');
    const details = document.getElementById('resultDetails');

    container.className = 'result-container ' + (result.status === 'fraud' ? 'result-fraud' : 'result-normal');
    container.style.display = 'block';

    if (result.verification_required) {
        icon.className = 'fas fa-hourglass-half';
        text.textContent = 'Pending Verification';
        title.style.color = '#856404';
        container.classList.remove('result-fraud');
        container.classList.add('result-normal');
    } else if (result.status === 'fraud') {
        icon.className = 'fas fa-exclamation-triangle';
        text.textContent = 'Fraud Detected';
        title.style.color = '#721c24';
        container.classList.add('result-fraud');
    } else {
        icon.className = 'fas fa-check-circle';
        text.textContent = 'Transaction Normal';
        title.style.color = '#155724';
        container.classList.remove('result-fraud');
        container.classList.add('result-normal');
    }

    details.innerHTML = `
        <div class="detail-item">
            <div class="detail-label">Sender ID</div>
            <div class="detail-value">${result.sender_id}</div>
        </div>
        <div class="detail-item">
            <div class="detail-label">Receiver ID</div>
            <div class="detail-value">${result.receiver_id}</div>
        </div>
        <div class="detail-item">
            <div class="detail-label">Amount</div>
            <div class="detail-value">$${result.amount.toFixed(2)}</div>
        </div>
        <div class="detail-item">
            <div class="detail-label">Fraud Probability</div>
            <div class="detail-value">${(result.probability * 100).toFixed(2)}%</div>
        </div>
        <div class="detail-item">
            <div class="detail-label">Error Balance Origin</div>
            <div class="detail-value">$${result.errorBalanceOrig.toFixed(2)}</div>
        </div>
        <div class="detail-item">
            <div class="detail-label">Error Balance Dest</div>
            <div class="detail-value">$${result.errorBalanceDest.toFixed(2)}</div>
        </div>
    `;

    if (result.verification_required) {
        document.getElementById('otpSection').style.display = 'block';
        document.getElementById('submitBtn').textContent = 'Make Payment';
        document.getElementById('submitBtn').disabled = true;
        showAlert('info', result.message);
    } else {
        showAlert('success', result.message);
        document.getElementById('submitBtn').textContent = 'Make Payment';
        document.getElementById('submitBtn').disabled = false;
        // reload form fields after successful non-fraud or post-second-step transaction
        document.getElementById('transactionForm').reset();
    }
}

function showAlert(type, message) {
    const alert = document.getElementById('alert');
    alert.className = `alert alert-${type}`;
    alert.textContent = message;
    alert.style.display = 'block';

    setTimeout(() => {
        alert.style.display = 'none';
    }, 5000);
}