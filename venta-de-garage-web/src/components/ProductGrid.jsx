import React, { useEffect, useState, useCallback } from 'react';
import { Grid, Typography, Box, CircularProgress, Button } from '@mui/material';
import ProductCard from './ProductCard';
import { fetchProducts, fetchCategories, fetchLocations, incrementProductSearch, incrementProductView } from '../services/api';
import { useTheme } from '@mui/material/styles';

// Nueva función para actualizar el estado 'featured' en el backend
async function updateFeatured(productId, isFeatured) {
    await fetch(`http://localhost:8000/products/${productId}/featured`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(isFeatured)
    });
}

const ProductGrid = ({ refreshTrigger = 0, searchTerm = '', category = '', originalSearchTerm = '', suggestion, onSuggestion, locationFilter = '', sellerIdFilter = null }) => {
    const [products, setProducts] = useState([]);
    const [total, setTotal] = useState(0);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [categories, setCategories] = useState([]);
    const [provinces, setProvinces] = useState([]);
    const [showAllCategories, setShowAllCategories] = useState(false);
    const [showAllProvinces, setShowAllProvinces] = useState(false);
    const initialFilters = {
        category: category || '',
        condition: '',
        location: '',
        priceMin: '',
        priceMax: '',
        endsIn: '',
    };
    const [filters, setFilters] = useState(initialFilters);
    const [localPrice, setLocalPrice] = useState({ min: '', max: '' });
    const [topFeatured, setTopFeatured] = useState([]);
    const [page, setPage] = useState(1);
    const pageSize = 15;
    const theme = useTheme();

    // Cargar categorías y ubicaciones al montar
    useEffect(() => {
        fetchCategories().then(setCategories).catch(() => setCategories([]));
        fetchLocations().then(locs => {
            if (locs && locs.provinces) {
                setProvinces(locs.provinces);
            } else {
                setProvinces([]);
            }
        }).catch(() => setProvinces([]));
    }, []);

    // Sincronizar el filtro de categoría con la prop 'category' si cambia
    useEffect(() => {
        setFilters(prev => ({ ...prev, category: category || '' }));
    }, [category]);

    // Sincronizar el estado local con los filtros globales cuando cambian
    useEffect(() => {
        setLocalPrice({ min: filters.priceMin, max: filters.priceMax });
    }, [filters.priceMin, filters.priceMax]);

    // Resetear filtros cuando cambia el searchTerm (búsqueda desde el buscador)
    useEffect(() => {
        setFilters(initialFilters);
        setPage(1);
    }, [searchTerm]);

    // Determinar si estamos en una búsqueda o en la página principal
    const hasActiveFilters = !!searchTerm || 
        !!filters.category || 
        !!filters.condition || 
        !!filters.location || 
        !!filters.priceMin || 
        !!filters.priceMax || 
        !!filters.endsIn ||
        !!locationFilter ||
        !!sellerIdFilter;

    useEffect(() => {
        const loadProducts = async () => {
            try {
                setLoading(true);
                const isMainPage = !hasActiveFilters;
                console.log('ProductGrid fetchProducts', { sellerIdFilter, locationFilter, searchTerm });
                const data = await fetchProducts({
                    searchTerm: (locationFilter || (sellerIdFilter !== null && sellerIdFilter !== undefined && sellerIdFilter !== '')) ? '' : searchTerm,
                    location: locationFilter ? locationFilter : (filters.location || ''),
                    seller_id: (sellerIdFilter !== null && sellerIdFilter !== undefined && sellerIdFilter !== '') ? Number(sellerIdFilter) : undefined,
                    ...filters,
                    ...(locationFilter ? { location: locationFilter } : {}),
                    featured_only: isMainPage,
                    page,
                    pageSize
                });
                setProducts(data.items);
                setTotal(data.total);
                setError(null);

                // Si estamos en la página principal, calcular los top 6 destacados
                if (isMainPage) {
                    // Ordenar por búsquedas descendente y tomar los 6 primeros
                    const sorted = [...data.items].sort((a, b) => (b.searches || 0) - (a.searches || 0));
                    const top6 = sorted.slice(0, 6);
                    setTopFeatured(top6);
                    // Marcar como destacados en el backend si no lo están
                    for (const prod of top6) {
                        if (!prod.featured) {
                            await updateFeatured(prod.id, true);
                        }
                    }
                    // Marcar el resto como no destacados si estaban destacados
                    for (const prod of sorted.slice(6)) {
                        if (prod.featured) {
                            await updateFeatured(prod.id, false);
                        }
                    }
                } else {
                    setTopFeatured([]);
                }

                // Incrementar búsquedas solo si es búsqueda
                if (hasActiveFilters) {
                    const alreadySearched = JSON.parse(sessionStorage.getItem('searchedProducts') || '[]');
                    const newIds = data.items
                        .map(p => p.id)
                        .filter(id => !alreadySearched.includes(id));

                    if (newIds.length > 0) {
                        await Promise.all(newIds.map(id => incrementProductSearch(id)));
                        sessionStorage.setItem('searchedProducts', JSON.stringify([...alreadySearched, ...newIds]));
                        
                        // Refrescar productos tras incrementar búsquedas
                        const refreshed = await fetchProducts({
                            searchTerm,
                            ...filters,
                            featured_only: isMainPage,
                            page,
                            pageSize
                        });
                        setProducts(refreshed.items);
                    }
                }

                // Incrementar vistas para cada producto mostrado
                const alreadyViewed = JSON.parse(sessionStorage.getItem('viewedProducts') || '[]');
                const newViewIds = data.items
                    .map(p => p.id)
                    .filter(id => !alreadyViewed.includes(id));

                if (newViewIds.length > 0) {
                    await Promise.all(newViewIds.map(id => incrementProductView(id)));
                    sessionStorage.setItem('viewedProducts', JSON.stringify([...alreadyViewed, ...newViewIds]));
                }
            } catch (err) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };
        loadProducts();
    }, [
        refreshTrigger,
        searchTerm,
        filters,
        hasActiveFilters,
        page,
        locationFilter,
        sellerIdFilter
    ]);

    // Handlers de filtros
    const handleFilterChange = (key, value) => {
        setFilters(prev => ({ ...prev, [key]: value }));
    };

    // Handler para los inputs locales
    const handleLocalPriceChange = (key, value) => {
        if (/^\d*$/.test(value)) {
            setLocalPrice(prev => ({ ...prev, [key]: value }));
        }
    };

    // Handler para aplicar el filtro de precio
    const handleApplyPrice = () => {
        setFilters(prev => ({ ...prev, priceMin: localPrice.min, priceMax: localPrice.max }));
    };

    const totalPages = Math.max(1, Math.ceil(total / pageSize));

    if (loading) {
        return (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
                <CircularProgress />
            </Box>
        );
    }

    if (error) {
        return (
            <Box sx={{ p: 4, textAlign: 'center' }}>
                <Typography color="error">Error: {error}</Typography>
            </Box>
        );
    }

    if (hasActiveFilters) {
        return (
            <>
                <Box sx={{ display: 'flex', bgcolor: '#f5f5f5', minHeight: '70vh', px: { xs: 0, md: 2 }, py: 4 }}>
                    {/* Sidebar de filtros */}
                    <Box sx={{ width: 260, minWidth: 200, maxWidth: 300, bgcolor: '#fff', borderRadius: 2, boxShadow: 1, p: 3, mr: 4, display: { xs: 'none', md: 'block' }, height: 'fit-content' }}>
                        <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 2 }}>
                            Filtros
                        </Typography>
                        {/* Categorías */}
                        <Box sx={{ mb: 3 }}>
                            <Typography variant="body2" sx={{ fontWeight: 'bold', mb: 1 }}>Categoría</Typography>
                            {(showAllCategories ? categories : categories.slice(0, 10)).map((cat) => (
                                <Box key={cat.value} sx={{ mb: 0.5 }}>
                                    <input type="radio" id={`cat-${cat.value}`} name="category" value={cat.value} checked={filters.category === cat.value} onChange={() => handleFilterChange('category', cat.value)} />
                                    <label htmlFor={`cat-${cat.value}`}>{cat.label}</label>
                                </Box>
                            ))}
                            {categories.length > 10 && !showAllCategories && (
                                <Button size="small" onClick={() => setShowAllCategories(true)}>Más...</Button>
                            )}
                            {showAllCategories && (
                                <Button size="small" onClick={() => setShowAllCategories(false)}>Menos</Button>
                            )}
                        </Box>
                        {/* Condición */}
                        <Box sx={{ mb: 3 }}>
                            <Typography variant="body2" sx={{ fontWeight: 'bold', mb: 1 }}>Condición</Typography>
                            {['Nuevo', 'Usado'].map(cond => (
                                <Box key={cond} sx={{ mb: 0.5 }}>
                                    <input type="radio" id={`cond-${cond}`} name="condition" value={cond} checked={filters.condition === cond} onChange={() => handleFilterChange('condition', cond)} />
                                    <label htmlFor={`cond-${cond}`}>{cond}</label>
                                </Box>
                            ))}
                        </Box>
                        {/* Ubicación (Provincias) */}
                        <Box sx={{ mb: 3 }}>
                            <Typography variant="body2" sx={{ fontWeight: 'bold', mb: 1 }}>Ubicación</Typography>
                            {(showAllProvinces ? provinces : provinces.slice(0, 10)).map((prov) => (
                                <Box key={prov.id} sx={{ mb: 0.5 }}>
                                    <input type="radio" id={`prov-${prov.id}`} name="location" value={prov.name} checked={filters.location === prov.name} onChange={() => handleFilterChange('location', prov.name)} />
                                    <label htmlFor={`prov-${prov.id}`}>{prov.name}</label>
                                </Box>
                            ))}
                            {provinces.length > 10 && !showAllProvinces && (
                                <Button size="small" onClick={() => setShowAllProvinces(true)}>Más...</Button>
                            )}
                            {showAllProvinces && (
                                <Button size="small" onClick={() => setShowAllProvinces(false)}>Menos</Button>
                            )}
                        </Box>
                        {/* Garage vence en */}
                        <Box sx={{ mb: 3 }}>
                            <Typography variant="body2" sx={{ fontWeight: 'bold', mb: 1 }}>Garage vence en</Typography>
                            {[
                                { label: 'Más de 30 días', value: '30+' },
                                { label: 'Más de 7 días', value: '7+' },
                                { label: 'Mañana', value: '1' },
                                { label: 'Hoy', value: '0' },
                            ].map(opt => (
                                <Box key={opt.value} sx={{ mb: 0.5 }}>
                                    <input type="radio" id={`endsin-${opt.value}`} name="endsIn" value={opt.value} checked={filters.endsIn === opt.value} onChange={() => handleFilterChange('endsIn', opt.value)} />
                                    <label htmlFor={`endsin-${opt.value}`}>{opt.label}</label>
                                </Box>
                            ))}
                        </Box>
                        {/* Precio */}
                        <Box>
                            <Typography variant="body2" sx={{ fontWeight: 'bold', mb: 1 }}>Precio</Typography>
                            <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                                <input type="text" placeholder="Mín" style={{ width: 60 }} value={localPrice.min} onChange={e => handleLocalPriceChange('min', e.target.value)} />
                                <span>-</span>
                                <input type="text" placeholder="Máx" style={{ width: 60 }} value={localPrice.max} onChange={e => handleLocalPriceChange('max', e.target.value)} />
                                <Button size="small" variant="text" color="primary" onClick={handleApplyPrice} sx={{ ml: 1, textTransform: 'none', p: 0, minWidth: 'auto' }}>Aplicar</Button>
                            </Box>
                        </Box>
                        {/* Limpiar filtros */}
                        <Box sx={{ mt: 3 }}>
                            <Button size="small" variant="outlined" onClick={() => setFilters({ category: '', condition: '', location: '', priceMin: '', priceMax: '', endsIn: '' })}>Limpiar filtros</Button>
                        </Box>
                    </Box>
                    {/* Contenido principal */}
                    <Box sx={{ flex: 1 }}>
                        <Typography variant="h5" sx={{ fontWeight: 'bold', mb: 2, display: 'flex', alignItems: 'center', gap: 2 }}>
                            {sellerIdFilter
                              ? `Resultados para vendedor seleccionado`
                              : (locationFilter || searchTerm)
                                ? `Resultados para "${locationFilter || searchTerm}"`
                                : 'Resultados'}
                            {!loading && suggestion && originalSearchTerm && suggestion !== originalSearchTerm && (
                                <span style={{ marginLeft: 16, fontWeight: 'normal', fontSize: '1rem' }}>
                                    ¿Quisiste decir: <Button variant="text" onClick={() => onSuggestion(suggestion)}>{suggestion}</Button>?
                                </span>
                            )}
                        </Typography>
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                            {total} resultado{total !== 1 ? 's' : ''}
                        </Typography>
                        {products.length === 0 ? (
                            <Box sx={{ p: 4, textAlign: 'center' }}>
                                <Typography variant="h6" color="text.secondary">
                                    No se encontraron productos
                                    {searchTerm && ` para "${searchTerm}"`}
                                    {filters.category && ` en la categoría "${filters.category}"`}
                                </Typography>
                            </Box>
                        ) : (
                            <>
                                {topFeatured.length > 0 && (
                                    <Box sx={{ width: '100%', maxWidth: 1280, margin: '0 auto', px: { xs: 1, sm: 2 }, mb: 4 }}>
                                        <Typography variant="h5" sx={{ fontWeight: 'bold', mb: 2 }}>Artículos destacados</Typography>
                                        <Grid container spacing={2} justifyContent="center" alignItems="stretch">
                                            {topFeatured.map((product) => (
                                                <Grid item xs={12} sm={6} md={4} lg={3} key={product.id} sx={{ display: 'flex' }}>
                                                    <ProductCard
                                                        title={product.title}
                                                        price={product.price}
                                                        description={product.description}
                                                        categories={product.categories?.map(c => c.name) || []}
                                                        endsAt={product.ends_at}
                                                        imageUrl={product.images.length > 0 ? `/uploads/${product.images[0].filename}` : '/placeholder.jpg'}
                                                        sellerName={product.seller.name}
                                                        sellerWhatsapp={product.seller.whatsapp}
                                                        available={product.available}
                                                        views={product.views}
                                                        searches={product.searches}
                                                        featured={true}
                                                        locality={product.locality}
                                                    />
                                                </Grid>
                                            ))}
                                        </Grid>
                                    </Box>
                                )}
                                <Grid container spacing={2} sx={{ width: '100%', maxWidth: 1280, margin: '0 auto', px: { xs: 1, sm: 2 } }} justifyContent="center" alignItems="stretch">
                                    {products
                                        .filter(p => !topFeatured.some(f => f.id === p.id))
                                        .map((product) => (
                                            <Grid item xs={12} sm={6} md={4} lg={3} key={product.id} sx={{ display: 'flex' }}>
                                                <ProductCard
                                                    title={product.title}
                                                    price={product.price}
                                                    description={product.description}
                                                    categories={product.categories?.map(c => c.name) || []}
                                                    endsAt={product.ends_at}
                                                    imageUrl={product.images.length > 0 ? `/uploads/${product.images[0].filename}` : '/placeholder.jpg'}
                                                    sellerName={product.seller.name}
                                                    sellerWhatsapp={product.seller.whatsapp}
                                                    available={product.available}
                                                    views={product.views}
                                                    searches={product.searches}
                                                    featured={product.featured}
                                                    locality={product.locality}
                                                />
                                            </Grid>
                                        ))}
                                </Grid>
                                {/* Paginación */}
                                {totalPages > 1 && (
                                    <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
                                        <Button
                                            variant="outlined"
                                            onClick={() => setPage(p => Math.max(1, p - 1))}
                                            disabled={page === 1}
                                            sx={{ mr: 2 }}
                                        >
                                            Anterior
                                        </Button>
                                        <Typography sx={{ alignSelf: 'center' }}>Página {page} de {totalPages}</Typography>
                                        <Button
                                            variant="outlined"
                                            onClick={() => setPage(p => (page < totalPages ? p + 1 : p))}
                                            disabled={page >= totalPages}
                                            sx={{ ml: 2 }}
                                        >
                                            Siguiente
                                        </Button>
                                    </Box>
                                )}
                            </>
                        )}
                    </Box>
                </Box>
            </>
        );
    }

    return (
        <>
            <Grid container spacing={2} sx={{ width: '100%', maxWidth: 1280, margin: '0 auto', px: { xs: 1, sm: 2 } }} justifyContent="center" alignItems="stretch">
                {products.map((product) => (
                    <Grid item xs={12} sm={6} md={4} lg={3} key={product.id} sx={{ display: 'flex' }}>
                        <ProductCard
                            title={product.title}
                            price={product.price}
                            description={product.description}
                            categories={product.categories?.map(c => c.name) || []}
                            endsAt={product.ends_at}
                            imageUrl={product.images.length > 0 ? `/uploads/${product.images[0].filename}` : '/placeholder.jpg'}
                            sellerName={product.seller.name}
                            sellerWhatsapp={product.seller.whatsapp}
                            available={product.available}
                            views={product.views}
                            searches={product.searches}
                            featured={product.featured}
                            locality={product.locality}
                        />
                    </Grid>
                ))}
            </Grid>
        </>
    );
};

export default ProductGrid; 
