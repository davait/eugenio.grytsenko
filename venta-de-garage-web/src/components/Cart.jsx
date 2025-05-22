import React from 'react';
import {
  Drawer,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Avatar,
  Typography,
  IconButton,
  Box,
  Button,
  Divider,
} from '@mui/material';
import { Delete as DeleteIcon, WhatsApp as WhatsAppIcon } from '@mui/icons-material';
import { useSelector, useDispatch } from 'react-redux';
import { removeFromCart } from '../features/cart/cartSlice';

const Cart = ({ open, onClose }) => {
  const cartItems = useSelector((state) => state.cart.items);
  const dispatch = useDispatch();

  const handleRemoveItem = (id) => {
    dispatch(removeFromCart(id));
  };

  return (
    <Drawer
      anchor="right"
      open={open}
      onClose={onClose}
      PaperProps={{
        sx: { width: { xs: '100%', sm: 400 } },
      }}
    >
      <Box sx={{ p: 2 }}>
        <Typography variant="h6" component="div" sx={{ mb: 2 }}>
          Artículos que te interesan ({cartItems.length})
        </Typography>
        <Divider />
        <List sx={{ mb: 2 }}>
          {cartItems.map((item) => (
            <ListItem
              key={item.id}
              secondaryAction={
                <IconButton
                  edge="end"
                  aria-label="delete"
                  onClick={() => handleRemoveItem(item.id)}
                >
                  <DeleteIcon />
                </IconButton>
              }
            >
              <ListItemAvatar>
                <Avatar
                  variant="square"
                  src={item.image}
                  alt={item.title}
                  sx={{ width: 60, height: 60, mr: 2 }}
                />
              </ListItemAvatar>
              <ListItemText
                primary={item.title}
                secondary={
                  <>
                    <Typography component="span" variant="body2" color="text.primary">
                      ${item.price}
                    </Typography>
                    <Typography component="p" variant="body2" color="text.secondary">
                      {item.location}
                    </Typography>
                  </>
                }
              />
            </ListItem>
          ))}
        </List>
        <Divider />
        <Box sx={{ mt: 2, mb: 2 }}>
          <Button
            variant="contained"
            fullWidth
            startIcon={<WhatsAppIcon />}
            sx={{
              backgroundColor: '#3483FA',
              '&:hover': {
                backgroundColor: '#2968c8',
              },
              fontWeight: 'bold',
              fontSize: '1.1rem',
            }}
          >
            Contactar vendedores
          </Button>
        </Box>
      </Box>
    </Drawer>
  );
};

export default Cart; 