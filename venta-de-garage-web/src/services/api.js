const API_URL = 'http://localhost:8000';

export const fetchProducts = async ({
    searchTerm = '',
    category = '',
    condition = '',
    location = '',
    locality = '',
    priceMin = '',
    priceMax = '',
    endsIn = '',
    featured_only = false,
    page = 1,
    pageSize = 15,
    seller_id = '',
} = {}) => {
    try {
        const url = new URL(`${API_URL}/products/`);
        
        // Añadir parámetros de búsqueda solo si tienen valor
        if (searchTerm) url.searchParams.append('search', searchTerm);
        if (category) url.searchParams.append('category', category);
        if (condition) url.searchParams.append('condition', condition);
        if (location) url.searchParams.append('location', location);
        if (locality) url.searchParams.append('locality', locality);
        if (priceMin !== '') url.searchParams.append('price_min', priceMin);
        if (priceMax !== '') url.searchParams.append('price_max', priceMax);
        if (endsIn) url.searchParams.append('ends_in', endsIn);
        if (seller_id !== undefined && seller_id !== null && seller_id !== '') url.searchParams.append('seller_id', seller_id);
        
        // Siempre incluir estos parámetros
        url.searchParams.append('active_only', 'true');
        url.searchParams.append('featured_only', featured_only.toString());
        url.searchParams.append('page', page);
        url.searchParams.append('page_size', pageSize);

        const response = await fetch(url);
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Error al obtener productos');
        }
        return await response.json(); // { items, total }
    } catch (error) {
        console.error('Error en fetchProducts:', error);
        throw error;
    }
};

export const createProduct = async (formData) => {
    try {
        const response = await fetch(`${API_URL}/products/`, {
            method: 'POST',
            body: formData, // FormData ya tiene el Content-Type correcto para archivos
        });
        
        if (!response.ok) {
            let errorMsg = 'Error al crear producto';
            try {
                const errorData = await response.json();
                if (errorData && errorData.detail) {
                    if (typeof errorData.detail === 'object') {
                        errorMsg = JSON.stringify(errorData.detail);
                    } else {
                        errorMsg = errorData.detail;
                    }
                }
            } catch (e) {}
            throw new Error(errorMsg);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Error:', error);
        throw error;
    }
};

export const getProductById = async (id) => {
    try {
        const response = await fetch(`${API_URL}/products/${id}`);
        if (!response.ok) {
            throw new Error('Error al obtener el producto');
        }
        return await response.json();
    } catch (error) {
        console.error('Error:', error);
        throw error;
    }
};

export const fetchCategories = async () => {
    const response = await fetch(`${API_URL}/categories`);
    if (!response.ok) throw new Error('Error al obtener categorías');
    return (await response.json()).categories;
};

export const fetchLocations = async () => {
    try {
        const response = await fetch(`${API_URL}/locations`);
        if (!response.ok) {
            throw new Error('Error al cargar las ubicaciones');
        }
        const data = await response.json();
        // Ahora data tiene { provinces: [...], localities: [...] }
        return data;
    } catch (error) {
        console.error('Error:', error);
        return { provinces: [], localities: [] };
    }
};

export const fetchProvinces = async () => {
    try {
        const response = await fetch(`${API_URL}/locations/provinces`);
        if (!response.ok) {
            throw new Error('Error al cargar las provincias');
        }
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error:', error);
        throw error;
    }
};

export const fetchLocalities = async (provinceId) => {
    try {
        const response = await fetch(`${API_URL}/locations/provinces/${provinceId}/localities`);
        if (!response.ok) {
            throw new Error('Error al cargar las localidades');
        }
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error:', error);
        throw error;
    }
};

export const incrementProductView = async (productId) => {
    const response = await fetch(`${API_URL}/products/${productId}/view`, { method: 'POST' });
    if (!response.ok) throw new Error('Error al incrementar vistas');
    return await response.json();
};

export const incrementProductSearch = async (productId) => {
    const response = await fetch(`${API_URL}/products/${productId}/search`, { method: 'POST' });
    if (!response.ok) throw new Error('Error al incrementar búsquedas');
    return await response.json();
}; 
