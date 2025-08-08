let searchInputs = [];
let currentFocus = -1;
let originalSearch = '';
let autocompleteResults = [];
let debounceTimeout;
let activeSearchInput = null;

document.addEventListener('DOMContentLoaded', function() {
    // Support both search bars
    const homeSearchBar = document.getElementById('search-bar');
    const resultsSearchBar = document.getElementById('search-bar-results');
    
    if (homeSearchBar) {
        searchInputs.push(homeSearchBar);
        homeSearchBar.addEventListener('input', () => handleUserInput(homeSearchBar));
        homeSearchBar.addEventListener('keydown', autocompleteInput);
        homeSearchBar.addEventListener('focus', () => { activeSearchInput = homeSearchBar; });
    }
    
    if (resultsSearchBar) {
        searchInputs.push(resultsSearchBar);
        resultsSearchBar.addEventListener('input', () => handleUserInput(resultsSearchBar));
        resultsSearchBar.addEventListener('keydown', autocompleteInput);
        resultsSearchBar.addEventListener('focus', () => { activeSearchInput = resultsSearchBar; });
    }
    
    currentFocus = -1;
    originalSearch = '';
    autocompleteResults = [];
    
    // Hide autocomplete when clicking outside
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.autocomplete')) {
            hideAutocomplete();
        }
    });
});

const handleUserInput = (inputElement) => {
    activeSearchInput = inputElement;
    const query = inputElement.value.trim();
    
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
    
    // Add to autocomplete container (find the one containing the active search input)
    const autocompleteContainer = activeSearchInput ? activeSearchInput.closest('.autocomplete') : document.querySelector('.autocomplete');
    if (autocompleteContainer) {
        autocompleteContainer.appendChild(autocompleteList);
    }
    
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
            submitSearch(activeSearchInput ? activeSearchInput.value.trim() : '');
        }
    } else if (e.key === 'Escape') {
        hideAutocomplete();
        if (activeSearchInput) activeSearchInput.blur();
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
    if (activeSearchInput) {
        activeSearchInput.value = suggestion;
        hideAutocomplete();
        activeSearchInput.focus();
    }
};

const submitSearch = (query) => {
    if (!query || query.trim() === '') {
        return;
    }
    
    // Submit the form
    const form = document.getElementById('search-form');
    if (form && activeSearchInput) {
        // Set the search input value
        activeSearchInput.value = query.trim();
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

// Function to clear search results input
const clearSearchResults = () => {
    const resultsSearchBar = document.getElementById('search-bar-results');
    if (resultsSearchBar) {
        resultsSearchBar.value = '';
        resultsSearchBar.focus();
        hideAutocomplete();
    }
};