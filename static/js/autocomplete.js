let searchInput, currentFocus, originalSearch, autocompleteResults;
let debounceTimeout;

document.addEventListener('DOMContentLoaded', function() {
    searchInput = document.getElementById('search-bar');
    currentFocus = -1;
    originalSearch = '';
    autocompleteResults = [];

    if (!searchInput) return;

    // Add event listeners
    searchInput.addEventListener('input', handleUserInput);
    searchInput.addEventListener('keydown', autocompleteInput);
    
    // Hide autocomplete when clicking outside
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.autocomplete')) {
            hideAutocomplete();
        }
    });
});

const handleUserInput = () => {
    const query = searchInput.value.trim();
    
    // Clear existing timeout
    clearTimeout(debounceTimeout);
    
    if (query.length === 0) {
        hideAutocomplete();
        return;
    }
    
    // Debounce the request to avoid spam
    debounceTimeout = setTimeout(() => {
        fetchSuggestions(query);
    }, 150);
};

const fetchSuggestions = async (query) => {
    try {
        const response = await fetch('/autocomplete', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ q: query })
        });
        
        if (response.ok) {
            const data = await response.json();
            autocompleteResults = data[1] || [];
            originalSearch = data[0] || query;
            updateAutocompleteList();
        } else {
            hideAutocomplete();
        }
    } catch (error) {
        console.error('Autocomplete error:', error);
        hideAutocomplete();
    }
};

const updateAutocompleteList = () => {
    // Remove existing autocomplete list
    const existingList = document.getElementById('autocomplete-list');
    if (existingList) {
        existingList.remove();
    }
    
    if (autocompleteResults.length === 0) {
        hideAutocomplete();
        return;
    }
    
    // Create new autocomplete list
    const autocompleteList = document.createElement('div');
    autocompleteList.id = 'autocomplete-list';
    
    autocompleteResults.forEach((suggestion, index) => {
        const suggestionDiv = document.createElement('div');
        suggestionDiv.innerHTML = `<i class="fas fa-magnifying-glass autocomplete-icon"></i>${highlightMatch(suggestion, originalSearch)}`;
        suggestionDiv.setAttribute('data-suggestion', suggestion);
        
        // Add click event
        suggestionDiv.addEventListener('click', function() {
            selectSuggestion(suggestion);
            submitSearch(suggestion);
        });
        
        autocompleteList.appendChild(suggestionDiv);
    });
    
    // Add to autocomplete container
    const autocompleteContainer = document.querySelector('.autocomplete');
    autocompleteContainer.appendChild(autocompleteList);
    
    // Apply connected styling
    autocompleteContainer.classList.add('has-suggestions');
    
    // Reset focus
    currentFocus = -1;
};

const highlightMatch = (text, query) => {
    if (!query) return text;
    
    const index = text.toLowerCase().indexOf(query.toLowerCase());
    if (index === -1) return text;
    
    const before = text.substring(0, index);
    const match = text.substring(index, index + query.length);
    const after = text.substring(index + query.length);
    
    return `${before}<strong>${match}</strong>${after}`;
};

const autocompleteInput = (e) => {
    const autocompleteList = document.getElementById('autocomplete-list');
    if (!autocompleteList) return;
    
    const items = autocompleteList.querySelectorAll('div');
    
    if (e.key === 'ArrowDown') {
        e.preventDefault();
        currentFocus++;
        if (currentFocus >= items.length) currentFocus = 0;
        setActiveItem(items);
    } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        currentFocus--;
        if (currentFocus < 0) currentFocus = items.length - 1;
        setActiveItem(items);
    } else if (e.key === 'Enter') {
        if (currentFocus > -1 && items[currentFocus]) {
            e.preventDefault();
            const suggestion = items[currentFocus].getAttribute('data-suggestion');
            selectSuggestion(suggestion);
            submitSearch(suggestion);
        } else {
            // No autocomplete item selected, submit current search
            e.preventDefault();
            submitSearch(searchInput.value.trim());
        }
    } else if (e.key === 'Escape') {
        hideAutocomplete();
        searchInput.blur();
    }
};

const setActiveItem = (items) => {
    // Remove active class from all items
    items.forEach(item => item.classList.remove('autocomplete-active'));
    
    // Add active class to current item
    if (currentFocus >= 0 && items[currentFocus]) {
        items[currentFocus].classList.add('autocomplete-active');
        
        // Scroll into view if necessary
        items[currentFocus].scrollIntoView({ 
            block: 'nearest', 
            behavior: 'smooth' 
        });
    }
};

const selectSuggestion = (suggestion) => {
    searchInput.value = suggestion;
    hideAutocomplete();
    searchInput.focus();
};

const submitSearch = (query) => {
    if (!query || query.trim() === '') {
        return;
    }
    
    // Submit the form
    const form = document.getElementById('search-form');
    if (form) {
        // Set the search input value
        searchInput.value = query.trim();
        form.submit();
    }
};

const hideAutocomplete = () => {
    const existingList = document.getElementById('autocomplete-list');
    if (existingList) {
        existingList.remove();
    }
    
    const autocompleteContainer = document.querySelector('.autocomplete');
    if (autocompleteContainer) {
        autocompleteContainer.classList.remove('has-suggestions');
    }
    
    currentFocus = -1;
};