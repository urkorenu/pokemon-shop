document.addEventListener('DOMContentLoaded', () => {
    // Get references to DOM elements
    const darkModeSwitch = document.getElementById('darkModeSwitch');
    const priceInput = document.getElementById('price');
    const followTcgCheckbox = document.getElementById('follow_tcg');
    const conditionSelect = document.getElementById('condition');
    const tcgWarning = document.getElementById('tcg_warning');
    const cardTypeDropdown = document.getElementById("card_type");

    /**
     * Apply the selected theme to the document body and save it to localStorage.
     * @param {string} theme - The theme to apply ('dark' or 'light').
     */
    function applyTheme(theme) {
        document.body.classList.toggle('bg-dark', theme === 'dark');
        document.body.classList.toggle('text-light', theme === 'dark');
        document.body.classList.toggle('bg-light', theme !== 'dark');
        document.body.classList.toggle('text-dark', theme !== 'dark');
        localStorage.setItem('theme', theme);
    }

    /**
     * Enforce the logic for condition and price input based on the followTcgCheckbox state.
     */
    function enforceConditionLogic() {
        const isDisabled = followTcgCheckbox.checked;
        conditionSelect.value = isDisabled ? "NM" : conditionSelect.value;
        conditionSelect.disabled = isDisabled;
        priceInput.value = isDisabled ? '' : priceInput.value;
        priceInput.disabled = isDisabled;
        tcgWarning.style.display = isDisabled ? 'block' : 'none';
    }

    /**
     * Fetch the TCGPlayer price for the specified card and update the price input.
     */
    async function fetchTCGPrice() {
        const setName = document.getElementById("set_name").value.trim();
        const cardNumber = document.getElementById("number").value.trim();
        const cardType = cardTypeDropdown.value.trim();

        if (!setName || !cardNumber || !cardType) {
            alert("Please fill Set Name, Card Number, and select Card Type to fetch the price.");
            followTcgCheckbox.checked = false;
            enforceConditionLogic();
            return;
        }

        try {
            const response = await fetch(`/seller/card-details?set_name=${encodeURIComponent(setName)}&number=${encodeURIComponent(cardNumber)}`);
            if (!response.ok) throw new Error("Failed to fetch card details");

            const data = await response.json();
            const tcgPriceUSD = parseFloat(data.prices?.[cardType.toLowerCase()]?.market || 0.0);
            if (tcgPriceUSD > 0) {
                priceInput.value = Math.round(tcgPriceUSD * 3.56);
            } else {
                throw new Error("TCGPlayer price not found for this card type.");
            }
        } catch (error) {
            alert("Failed to fetch TCGPlayer price. Please try again.");
            followTcgCheckbox.checked = false;
            enforceConditionLogic();
        }
    }

    /**
     * Fetch the card details based on the set name and card number, and update the form fields.
     */
    async function fetchCardDetails() {
        const setName = document.getElementById("set_name").value;
        const cardNumber = document.getElementById("number").value;

        document.getElementById("name").value = "";
        cardTypeDropdown.innerHTML = '<option value="">Select Card Type</option>';

        if (!setName || !cardNumber) return;

        try {
            const response = await fetch(`/seller/card-details?set_name=${encodeURIComponent(setName)}&number=${encodeURIComponent(cardNumber)}`);
            if (!response.ok) return;

            const data = await response.json();
            if (data.error) return;

            document.getElementById("name").value = data.name;
            data.types.forEach(type => {
                const option = document.createElement("option");
                option.value = type;
                option.textContent = type.replace("_", " ").toUpperCase();
                cardTypeDropdown.appendChild(option);
            });
        } catch (error) {
            console.error("Error fetching card details:", error);
        }
    }

    /**
     * Toggle between login and registration forms.
     */
    function toggleAuthForms() {
        const loginForm = document.getElementById('login-form');
        const registerForm = document.getElementById('register-form');
        const formTitle = document.getElementById('form-title');
        const toggleLink = document.getElementById('toggle-link');
        const toggleText = document.getElementById('toggle-text');

        toggleLink.addEventListener('click', (e) => {
            e.preventDefault();
            const isLoginVisible = loginForm.style.display !== 'none';
            loginForm.style.display = isLoginVisible ? 'none' : 'block';
            registerForm.style.display = isLoginVisible ? 'block' : 'none';
            formTitle.textContent = isLoginVisible ? registerForm.dataset.registerText : loginForm.dataset.loginText;
            toggleText.textContent = isLoginVisible ? registerForm.dataset.haveAccountText : loginForm.dataset.noAccountText;
            toggleLink.textContent = isLoginVisible ? registerForm.dataset.loginHereText : loginForm.dataset.registerHereText;
        });
    }

    /**
     * Show the card image in a modal.
     * @param {string} imageUrl - The URL of the card image.
     * @param {string} cardName - The name of the card.
     */
    function showCardImage(imageUrl, cardName) {
        document.getElementById('cardImage').src = imageUrl;
        document.getElementById('modalCardTitle').innerText = cardName || "Card";
        new bootstrap.Modal(document.getElementById('cardViewModal')).show();
    }

    // Apply the saved theme on page load
    const savedTheme = localStorage.getItem('theme') || 'light';
    applyTheme(savedTheme);

    // Event listener for dark mode switch
    darkModeSwitch.addEventListener('click', () => applyTheme(document.body.classList.contains('bg-dark') ? 'light' : 'dark'));

    // Event listener for follow TCG checkbox
    followTcgCheckbox.addEventListener('change', async () => {
        enforceConditionLogic();
        if (followTcgCheckbox.checked) await fetchTCGPrice();
    });

    // Event listener for condition select
    conditionSelect.addEventListener('change', () => {
        if (conditionSelect.value !== "NM") {
            followTcgCheckbox.checked = false;
            followTcgCheckbox.disabled = true;
            enforceConditionLogic();
        } else {
            followTcgCheckbox.disabled = false;
        }
    });

    // Event listener for form submission
    document.querySelector('form').addEventListener('submit', (e) => {
        if (!priceInput.value && !followTcgCheckbox.checked) {
            e.preventDefault();
            alert('You must either enter a manual price or choose to follow TCGPlayer price.');
        }
    });

    // Event listeners for fetching card details
    document.getElementById("set_name").addEventListener("input", fetchCardDetails);
    document.getElementById("number").addEventListener("input", fetchCardDetails);

    // Event listener for graded checkbox
    document.getElementById("is_graded").addEventListener("change", function () {
        document.getElementById("graded_fields").style.display = this.checked ? "block" : "none";
    });

    // Initialize the authentication form toggle functionality
    toggleAuthForms();
});