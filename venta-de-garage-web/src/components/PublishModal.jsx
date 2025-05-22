import React, { useState, useEffect } from 'react';
import {
    Modal,
    Box,
    Typography,
    TextField,
    Button,
    IconButton,
    Stack,
    InputAdornment,
    Select,
    MenuItem,
    FormControl,
    InputLabel,
} from '@mui/material';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { DateTimePicker } from '@mui/x-date-pickers/DateTimePicker';
import CloseIcon from '@mui/icons-material/Close';
import ImageIcon from '@mui/icons-material/Image';
import { createProduct } from '../services/api';
import { es } from 'date-fns/locale';
import LocationSelect from './LocationSelect';

const API_URL = 'http://localhost:8000';

const style = {
    position: 'absolute',
    top: '50%',
    left: '50%',
    transform: 'translate(-50%, -50%)',
    width: '90%',
    maxWidth: 600,
    bgcolor: 'background.paper',
    boxShadow: 24,
    p: 4,
    borderRadius: 2,
    maxHeight: '90vh',
    overflow: 'auto',
};

const PublishModal = ({ open, onClose, onPublished }) => {
    const [formData, setFormData] = useState({
        title: '',
        description: '',
        price: '',
        locality_id: '',
        categories: [],
        condition: '',
        ends_at: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000), // 30 días desde ahora
        seller_name: '',
        seller_whatsapp: '',
    });
    const [images, setImages] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [categories, setCategories] = useState([]);

    useEffect(() => {
        const fetchCategories = async () => {
            try {
                const response = await fetch(`${API_URL}/categories`);
                const data = await response.json();
                setCategories(data.categories);
            } catch (error) {
                console.error('Error fetching categories:', error);
            }
        };
        fetchCategories();
    }, []);

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        if (name === 'categories') {
            setFormData(prev => ({
                ...prev,
                categories: value
            }));
        } else {
            setFormData(prev => ({
                ...prev,
                [name]: value
            }));
        }
    };

    const handleDateChange = (newValue) => {
        setFormData(prev => ({
            ...prev,
            ends_at: newValue
        }));
    };

    const handleImageChange = (e) => {
        const files = Array.from(e.target.files);
        setImages(files);
    };

    const handleLocationChange = (value) => {
        setFormData(prev => ({
            ...prev,
            locality_id: value
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        // Validar que haya al menos una imagen
        if (images.length === 0) {
            setError('Debes seleccionar al menos una imagen.');
            setLoading(false);
            return;
        }

        try {
            const submitFormData = new FormData();
            // Agregar campos de texto
            Object.keys(formData).forEach(key => {
                if (key === 'ends_at') {
                    submitFormData.append(key, formData[key].toISOString());
                } else if (key === 'price') {
                    submitFormData.append(key, parseFloat(formData[key]));
                } else if (key === 'categories') {
                    formData.categories.forEach(cat => submitFormData.append('categories', cat));
                } else if (key === 'locality_id') {
                    submitFormData.append('locality_id', formData.locality_id);
                } else {
                    submitFormData.append(key, formData[key]);
                }
            });
            // Agregar imágenes
            images.forEach(image => {
                submitFormData.append('images', image);
            });

            await createProduct(submitFormData);
            // Limpiar el formulario
            setFormData({
                title: '',
                description: '',
                price: '',
                locality_id: '',
                categories: [],
                condition: '',
                ends_at: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000),
                seller_name: '',
                seller_whatsapp: '',
            });
            setImages([]);
            // Cerrar el modal y notificar la publicación exitosa
            onClose();
            onPublished();
        } catch (err) {
            // Mostrar el mensaje de error real del backend si existe
            if (err && err.message) {
                setError(err.message);
            } else {
            setError('Error al publicar el artículo. Por favor, intente nuevamente.');
            }
        } finally {
            setLoading(false);
        }
    };

    return (
        <LocalizationProvider dateAdapter={AdapterDateFns} adapterLocale={es}>
            <Modal
                open={open}
                onClose={onClose}
                aria-labelledby="modal-publish-title"
            >
                <Box sx={style}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                        <Typography id="modal-publish-title" variant="h6" component="h2">
                            Publicar Artículo
                        </Typography>
                        <IconButton onClick={onClose}>
                            <CloseIcon />
                        </IconButton>
                    </Box>

                    <form onSubmit={handleSubmit}>
                        <Stack spacing={3}>
                            <TextField
                                required
                                fullWidth
                                label="Título"
                                name="title"
                                value={formData.title}
                                onChange={handleInputChange}
                            />
                            
                            <TextField
                                required
                                fullWidth
                                label="Descripción"
                                name="description"
                                multiline
                                rows={4}
                                value={formData.description}
                                onChange={handleInputChange}
                            />
                            
                            <TextField
                                required
                                fullWidth
                                label="Precio"
                                name="price"
                                type="number"
                                InputProps={{
                                    startAdornment: <InputAdornment position="start">$</InputAdornment>,
                                }}
                                value={formData.price}
                                onChange={handleInputChange}
                            />
                            
                            <LocationSelect
                                value={formData.locality_id}
                                onChange={handleLocationChange}
                                required
                            />

                            <FormControl fullWidth required>
                                <InputLabel id="category-label">Categorías</InputLabel>
                                <Select
                                    labelId="category-label"
                                    name="categories"
                                    multiple
                                    value={formData.categories}
                                    label="Categorías"
                                    onChange={handleInputChange}
                                    renderValue={(selected) => selected.map(val => val).join(', ')}
                                >
                                    {categories.map((category) => (
                                        <MenuItem key={category.value} value={category.value}>
                                            {category.label}
                                        </MenuItem>
                                    ))}
                                </Select>
                            </FormControl>

                            <FormControl fullWidth required>
                                <InputLabel id="condition-label">Condición</InputLabel>
                                <Select
                                    labelId="condition-label"
                                    name="condition"
                                    value={formData.condition || ''}
                                    label="Condición"
                                    onChange={handleInputChange}
                                >
                                    <MenuItem value="Nuevo">Nuevo</MenuItem>
                                    <MenuItem value="Usado">Usado</MenuItem>
                                </Select>
                            </FormControl>

                            <DateTimePicker
                                label="Finaliza el"
                                value={formData.ends_at}
                                onChange={handleDateChange}
                                renderInput={(params) => <TextField {...params} required fullWidth />}
                                minDateTime={new Date()}
                            />

                            <TextField
                                required
                                fullWidth
                                label="Nombre del vendedor"
                                name="seller_name"
                                value={formData.seller_name}
                                onChange={handleInputChange}
                            />

                            <TextField
                                required
                                fullWidth
                                label="WhatsApp"
                                name="seller_whatsapp"
                                value={formData.seller_whatsapp}
                                onChange={handleInputChange}
                                placeholder="+5491122334455"
                            />

                            <Box>
                                <input
                                    accept="image/*"
                                    style={{ display: 'none' }}
                                    id="image-upload"
                                    type="file"
                                    multiple
                                    onChange={handleImageChange}
                                />
                                <label htmlFor="image-upload">
                                    <Button
                                        variant="outlined"
                                        component="span"
                                        startIcon={<ImageIcon />}
                                        fullWidth
                                    >
                                        Seleccionar Imágenes
                                    </Button>
                                </label>
                                {images.length > 0 && (
                                    <Typography variant="body2" sx={{ mt: 1 }}>
                                        {images.length} imagen(es) seleccionada(s)
                                    </Typography>
                                )}
                            </Box>

                            {error && (
                                <Typography color="error" variant="body2">
                                    {error}
                                </Typography>
                            )}

                            <Button
                                type="submit"
                                variant="contained"
                                fullWidth
                                disabled={loading}
                            >
                                {loading ? 'Publicando...' : 'Publicar'}
                            </Button>
                        </Stack>
                    </form>
                </Box>
            </Modal>
        </LocalizationProvider>
    );
};

export default PublishModal; 