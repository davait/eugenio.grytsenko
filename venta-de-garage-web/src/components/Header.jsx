import React, { useState, useEffect, useRef } from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  InputBase,
  IconButton,
  Badge,
  Box,
  styled,
  useTheme,
  useMediaQuery,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ClickAwayListener,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Button,
  Avatar,
  Menu,
  MenuItem as DropdownMenuItem,
} from '@mui/material';
import {
  Search as SearchIcon,
  ShoppingCart as ShoppingCartIcon,
  Favorite as FavoriteIcon,
  Person as PersonIcon,
  History as HistoryIcon,
  LocationOn as LocationIcon,
  Category as CategoryIcon,
} from '@mui/icons-material';
import { useSelector } from 'react-redux';
import { useAuth } from '../contexts/AuthContext';
import { logout } from '../services/authService';

const API_URL = 'http://localhost:8000';

const Search = styled('div')(({ theme }) => ({
  position: 'relative',
  borderRadius: theme.shape.borderRadius,
  backgroundColor: '#FFFFFF',
  width: '100%',
  display: 'flex',
  alignItems: 'center',
  [theme.breakpoints.up('sm')]: {
    marginLeft: theme.spacing(3),
    width: 'auto',
  },
}));

const SearchIconWrapper = styled('div')(({ theme }) => ({
  padding: theme.spacing(0, 2),
  height: '100%',
  position: 'absolute',
  pointerEvents: 'none',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  color: '#666666',
}));

const StyledInputBase = styled(InputBase)(({ theme }) => ({
  color: '#333333',
  width: '100%',
  '& .MuiInputBase-input': {
    padding: theme.spacing(1, 1, 1, 0),
    paddingLeft: `calc(1em + ${theme.spacing(4)})`,
    transition: theme.transitions.create('width'),
    width: '100%',
    [theme.breakpoints.up('md')]: {
      width: '40ch',
      '&:focus': {
        width: '50ch',
      },
    },
  },
}));

const SuggestionsPanel = styled(Paper)(({ theme }) => ({
  position: 'absolute',
  top: '100%',
  left: 0,
  right: 0,
  zIndex: 1000,
  marginTop: theme.spacing(1),
  maxHeight: '400px',
  overflow: 'auto',
}));

const Header = ({ 
  onCartClick, 
  onSearch, 
  onOriginalSearchChange, 
  suggestion, 
  onSuggestionClick,
  onLoginClick,
  onRegisterClick 
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [recentSearches, setRecentSearches] = useState([]);
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('');
  const searchRef = useRef(null);
  const cartItems = useSelector((state) => state.cart.items);
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);
  const [liveSuggestion, setLiveSuggestion] = useState(null);
  const { user, setUser } = useAuth();
  const [anchorEl, setAnchorEl] = useState(null);
  const open = Boolean(anchorEl);

  useEffect(() => {
    // Cargar búsquedas recientes del localStorage
    const savedSearches = localStorage.getItem('recentSearches');
    if (savedSearches) {
      setRecentSearches(JSON.parse(savedSearches));
    }

    // Cargar categorías
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

  const fetchSuggestions = async (query) => {
    if (query.length < 2) {
      setSuggestions([]);
      setLiveSuggestion(null);
      setLoadingSuggestions(false);
      return;
    }
    setLoadingSuggestions(true);
    try {
      const url = new URL(`${API_URL}/search/suggestions`);
      url.searchParams.append('query', query);
      if (selectedCategory) {
        url.searchParams.append('category', selectedCategory);
      }
      const response = await fetch(url);
      const data = await response.json();
      setSuggestions(data.suggestions);
      setLiveSuggestion(data.suggestion || null);
    } catch (error) {
      console.error('Error fetching suggestions:', error);
    } finally {
      setLoadingSuggestions(false);
    }
  };

  const handleSearchChange = (event) => {
    const value = event.target.value;
    setSearchTerm(value);
    if (onOriginalSearchChange) onOriginalSearchChange(value);
    setShowSuggestions(true);
    fetchSuggestions(value);
  };

  const handleCategoryChange = (event) => {
    const category = event.target.value;
    setSelectedCategory(category);
    onSearch(searchTerm, category);
  };

  const handleSearchSubmit = (term, type = null, extra = {}) => {
    // Guardar en búsquedas recientes
    const newRecentSearches = [term, ...recentSearches.filter(s => s !== term)].slice(0, 5);
    setRecentSearches(newRecentSearches);
    localStorage.setItem('recentSearches', JSON.stringify(newRecentSearches));
    setSearchTerm(term);
    setShowSuggestions(false);
    if (type === 'ubicación') {
      onSearch('', selectedCategory, term);
    } else if (type === 'vendedor') {
      const sellerId = extra.seller_id !== undefined && extra.seller_id !== null ? Number(extra.seller_id) : null;
      onSearch('', selectedCategory, '', sellerId);
    } else {
      onSearch(term, selectedCategory);
    }
  };

  const handleKeyPress = (event) => {
    if (event.key === 'Enter') {
      handleSearchSubmit(searchTerm);
    }
  };

  const handleMenuClick = (event) => {
    setAnchorEl(event.currentTarget);
  };
  const handleMenuClose = () => {
    setAnchorEl(null);
  };
  const handleLogout = () => {
    logout();
    setUser(null);
    handleMenuClose();
    window.location.reload();
  };

  return (
    <AppBar position="static" sx={{ backgroundColor: '#FFE600' }}>
      <Toolbar>
        <Typography
          variant="h6"
          component="div"
          sx={{
            color: '#333333',
            fontWeight: 'bold',
            fontSize: isMobile ? '1.2rem' : '1.5rem',
          }}
        >
          Venta de Garage
        </Typography>

        <Box sx={{ 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          flex: 1,
          mx: 2
        }}>
          <ClickAwayListener onClickAway={() => setShowSuggestions(false)}>
            <Search>
              <SearchIconWrapper>
                <SearchIcon />
              </SearchIconWrapper>
              <StyledInputBase
                placeholder="Buscar artículos, garages y más..."
                value={searchTerm}
                onChange={handleSearchChange}
                onKeyPress={handleKeyPress}
                onFocus={() => setShowSuggestions(true)}
              />
              {showSuggestions && (searchTerm.length > 0 || recentSearches.length > 0) && (
                <SuggestionsPanel>
                  <List>
                    {searchTerm.length < 2 && recentSearches.map((search, index) => (
                      <ListItem
                        key={index}
                        button
                        onClick={() => handleSearchSubmit(search)}
                      >
                        <ListItemIcon>
                          <HistoryIcon />
                        </ListItemIcon>
                        <ListItemText primary={search} />
                      </ListItem>
                    ))}
                    {loadingSuggestions && searchTerm.length >= 2 && (
                      <ListItem>
                        <ListItemText primary="Buscando..." />
                      </ListItem>
                    )}
                    {!loadingSuggestions && searchTerm.length >= 2 && suggestions.length === 0 && (
                      <ListItem>
                        <ListItemText primary="¿Qué tenés ganas de llevarte hoy?" />
                      </ListItem>
                    )}
                    {/* Sugerencia ortográfica como primera opción */}
                    {liveSuggestion && liveSuggestion !== searchTerm && !suggestions.some(s => s.text && s.text.toLowerCase() === liveSuggestion.toLowerCase()) && (
                      <ListItem
                        button
                        onClick={() => handleSearchSubmit(liveSuggestion)}
                        sx={{ bgcolor: '#e3f2fd' }}
                      >
                        <ListItemIcon>
                          <SearchIcon />
                        </ListItemIcon>
                        <ListItemText 
                          primary={<span>¿Quisiste decir: <b>{liveSuggestion}</b>?</span>}
                          secondary="Sugerencia ortográfica"
                        />
                      </ListItem>
                    )}
                    {suggestions.map((suggestion, index) => (
                      <ListItem
                        key={index}
                        button
                        onClick={() => handleSearchSubmit(suggestion.text, suggestion.type, suggestion)}
                      >
                        <ListItemIcon>
                          {suggestion.type === 'ubicación' ? <LocationIcon /> : suggestion.type === 'vendedor' ? <PersonIcon /> : <CategoryIcon />}
                        </ListItemIcon>
                        <ListItemText 
                          primary={suggestion.text}
                          secondary={
                            suggestion.type === 'ubicación'
                              ? 'Ubicación'
                              : suggestion.type === 'vendedor'
                                ? 'Vendedor'
                                : suggestion.category || 'Otros'
                          }
                        />
                      </ListItem>
                    ))}
                  </List>
                </SuggestionsPanel>
              )}
            </Search>
          </ClickAwayListener>
        </Box>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          {user ? (
            <>
              <Button
                startIcon={<Avatar sx={{ width: 28, height: 28 }}>{user.name?.[0] || <PersonIcon />}</Avatar>}
                onClick={handleMenuClick}
                sx={{
                  color: '#333333',
                  textTransform: 'none',
                  fontWeight: 'medium',
                  '&:hover': {
                    backgroundColor: 'rgba(0, 0, 0, 0.04)',
                  },
                }}
              >
                {user.name}
              </Button>
              <Menu
                anchorEl={anchorEl}
                open={open}
                onClose={handleMenuClose}
                anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
                transformOrigin={{ vertical: 'top', horizontal: 'right' }}
              >
                <DropdownMenuItem onClick={handleLogout}>Salir</DropdownMenuItem>
              </Menu>
            </>
          ) : (
            <>
              <Button
                variant="text"
                onClick={onRegisterClick}
                sx={{
                  color: '#333333',
                  textTransform: 'none',
                  fontWeight: 'medium',
                  '&:hover': {
                    backgroundColor: 'rgba(0, 0, 0, 0.04)',
                  },
                }}
              >
                Creá tu cuenta
              </Button>
              <Button
                variant="text"
                onClick={onLoginClick}
                sx={{
                  color: '#333333',
                  textTransform: 'none',
                  fontWeight: 'medium',
                  '&:hover': {
                    backgroundColor: 'rgba(0, 0, 0, 0.04)',
                  },
                }}
              >
                Ingresá
              </Button>
            </>
          )}
          <IconButton
            color="inherit"
            onClick={onCartClick}
            sx={{
              color: '#333333',
              '&:hover': {
                backgroundColor: 'rgba(0, 0, 0, 0.04)',
              },
            }}
          >
            <Badge badgeContent={cartItems.length} color="error">
              <ShoppingCartIcon />
            </Badge>
          </IconButton>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Header; 
