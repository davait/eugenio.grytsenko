import React, { useState, useEffect } from 'react';
import {
    Card,
    CardContent,
    CardMedia,
    Typography,
    Button,
    Box,
    Chip,
    IconButton,
    CardActions,
} from '@mui/material';
import WhatsAppIcon from '@mui/icons-material/WhatsApp';
import LocationOnIcon from '@mui/icons-material/LocationOn';
import CategoryIcon from '@mui/icons-material/Category';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import StarIcon from '@mui/icons-material/Star';
import VisibilityIcon from '@mui/icons-material/Visibility';
import SearchIcon from '@mui/icons-material/Search';

const API_URL = 'http://localhost:8000';

const ProductCard = ({
    title,
    price,
    description,
    location,
    categories = [],
    endsAt,
    imageUrl,
    sellerName,
    sellerWhatsapp,
    available,
    views,
    searches,
    featured,
    locality
}) => {
    const formatLocation = () => {
        if (!locality) return 'Ubicación no disponible';
        return locality.province_name
            ? `${locality.name}, ${locality.province_name}`
            : locality.name;
    };

    const handleWhatsAppClick = () => {
        const message = `¡Hola! Me interesa tu producto "${title}" publicado en Venta de Garage`;
        const whatsappUrl = `https://wa.me/${sellerWhatsapp.replace(/[^0-9]/g, '')}?text=${encodeURIComponent(message)}`;
        window.open(whatsappUrl, '_blank');
    };

    const formatDate = (dateString) => {
        const date = new Date(dateString);
        return date.toLocaleDateString('es-AR', {
            day: 'numeric',
            month: 'short',
            year: 'numeric'
        });
    };

    const isExpired = new Date(endsAt) < new Date();

    // Construir la URL completa de la imagen
    const fullImageUrl = imageUrl.startsWith('http') 
        ? imageUrl 
        : imageUrl.startsWith('/uploads') 
            ? `${API_URL}${imageUrl}`
            : `${API_URL}/static/placeholder.jpg`;

    // Calcular tiempo restante
    const getTimeLeft = (endsAt) => {
        const now = new Date();
        const end = new Date(endsAt);
        const diffMs = end - now;
        if (diffMs <= 0) return 'Expirado';
        const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
        const diffHours = Math.floor((diffMs % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        return `${diffDays}d ${diffHours}h`;
    };

    return (
        <Card sx={{ 
            width: 400,
            minWidth: 400,
            maxWidth: 400,
            minHeight: 520,
            maxHeight: 560,
            display: 'flex',
            flexDirection: 'column',
            backgroundColor: '#fff',
            borderRadius: 3,
            boxShadow: '0 2px 12px rgba(0,0,0,0.10)',
            opacity: isExpired ? 0.7 : 1,
            '&:hover': {
                boxShadow: 8,
                transform: 'translateY(-4px)',
                transition: 'all 0.3s ease-in-out'
            }
        }}>
            <Box sx={{ position: 'relative' }}>
                <CardMedia
                    component="img"
                    image={fullImageUrl}
                    alt={title}
                    sx={{ objectFit: 'cover', height: 170, width: '100%', borderTopLeftRadius: 12, borderTopRightRadius: 12 }}
                />
                {featured && (
                    <StarIcon sx={{ position: 'absolute', top: 8, right: 8, color: '#FFD600', fontSize: 32, zIndex: 2 }} titleAccess="Destacado" />
                )}
            </Box>
            <CardContent sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', justifyContent: 'space-between', p: 2, minHeight: 0 }}>
                <Box sx={{ mb: 1, display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                    {categories.map((cat, idx) => (
                        <Chip
                            key={cat + idx}
                            icon={<CategoryIcon />}
                            label={cat}
                            size="small"
                            color="primary"
                        />
                    ))}
                </Box>
                <Box sx={{ mb: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Chip
                        icon={<AccessTimeIcon />}
                        label={available ? 'Disponible' : 'No disponible'}
                        size="small"
                        color={available ? 'success' : 'error'}
                        sx={{ ml: 0 }}
                    />
                    <Typography variant="caption" color="text.secondary" sx={{ ml: 0.5 }}>
                        {getTimeLeft(endsAt)}
                    </Typography>
                </Box>
                
                <Typography 
                    gutterBottom 
                    variant="h6" 
                    component="h2" 
                    sx={{ 
                        fontWeight: 'bold', 
                        display: '-webkit-box', 
                        WebkitLineClamp: 1, 
                        WebkitBoxOrient: 'vertical', 
                        overflow: 'hidden', 
                        textOverflow: 'ellipsis',
                        minHeight: '1.4em'
                    }}
                >
                    {title}
                </Typography>
                <Typography 
                    variant="h5" 
                    sx={{ 
                        mb: 2, 
                        fontWeight: 'bold',
                        color: '#333333',
                        display: 'flex',
                        alignItems: 'center',
                        gap: 1
                    }}
                >
                    {price === 0 ? (
                        <span style={{ position: 'relative', display: 'inline-block' }}>
                            Gratis
                            <span style={{
                                position: 'absolute',
                                top: '-0.3em',
                                right: '-2.1em',
                                background: '#ff1744',
                                color: 'white',
                                borderRadius: '8px',
                                fontSize: '0.48em',
                                fontWeight: 'bold',
                                padding: '0.5px 3px',
                                boxShadow: '0 1px 4px rgba(0,0,0,0.10)',
                                letterSpacing: 1,
                                zIndex: 1
                            }}>Hot</span>
                        </span>
                    ) : (
                        `$${price.toLocaleString()}`
                    )}
                </Typography>
                <Typography 
                    variant="body2" 
                    color="text.secondary" 
                    sx={{ mb: 2, display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden', minHeight: '2.8em' }}
                >
                    {description}
                </Typography>
                <Box sx={{ mb: 1 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 0.5 }}>
                        <LocationOnIcon sx={{ fontSize: 20, mr: 1, color: 'text.secondary' }} />
                        <Typography variant="body2" color="text.secondary">
                            {formatLocation()}
                        </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                            <VisibilityIcon sx={{ fontSize: 18, color: 'text.secondary' }} />
                            <Typography variant="caption" color="text.secondary">{views ?? 0}</Typography>
                        </Box>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                            <SearchIcon sx={{ fontSize: 18, color: 'text.secondary' }} />
                            <Typography variant="caption" color="text.secondary">{searches ?? 0}</Typography>
                        </Box>
                    </Box>
                </Box>
                <Box sx={{ mt: 'auto' }}>
                    <Typography variant="body2" sx={{ mb: 1 }}>
                        Vendedor: {sellerName}
                    </Typography>
                    <Button
                        variant="contained"
                        startIcon={<WhatsAppIcon />}
                        fullWidth
                        onClick={handleWhatsAppClick}
                        disabled={isExpired}
                        sx={{
                            backgroundColor: '#3483FA',
                            color: 'white',
                            fontWeight: 'bold',
                            '&:hover': {
                                backgroundColor: '#2968c8'
                            }
                        }}
                    >
                        ¡LO QUIERO!
                    </Button>
                </Box>
            </CardContent>
        </Card>
    );
};

export default ProductCard; 