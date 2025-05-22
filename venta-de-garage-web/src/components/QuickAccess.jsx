import React from 'react';
import { Box, Container, Paper, Typography } from '@mui/material';
import {
  LocalOffer as OfferIcon,
  CreditCard as CreditCardIcon,
  LocalFireDepartment as FireIcon,
  CardGiftcard as GiftIcon,
  ShoppingCart as CartIcon,
  LocalShipping as ShippingIcon,
} from '@mui/icons-material';

const quickAccessItems = [
  { icon: <FireIcon />, text: '¡Ofertas!', color: '#FF4E4E' },
  { icon: <CreditCardIcon />, text: 'Cuotas', color: '#00A650' },
  { icon: <OfferIcon />, text: 'Descuentos', color: '#3483FA' },
  { icon: <GiftIcon />, text: 'Regalos', color: '#FF7733' },
  { icon: <CartIcon />, text: 'Carrito', color: '#6B4CE6' },
  { icon: <ShippingIcon />, text: 'Envíos', color: '#00C1B4' },
];

const QuickAccess = () => {
  return (
    <Container sx={{ mb: 4 }}>
      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: {
            xs: 'repeat(2, 1fr)',
            sm: 'repeat(3, 1fr)',
            md: 'repeat(6, 1fr)',
          },
          gap: 2,
          py: 3,
        }}
      >
        {quickAccessItems.map((item, index) => (
          <Paper
            key={index}
            elevation={1}
            sx={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              p: 2,
              cursor: 'pointer',
              transition: 'transform 0.2s',
              aspectRatio: '1/1',
              '&:hover': {
                transform: 'translateY(-5px)',
              },
            }}
          >
            <Box
              sx={{
                backgroundColor: `${item.color}15`,
                borderRadius: '50%',
                p: 2,
                mb: 2,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: '60px',
                height: '60px',
              }}
            >
              <Box sx={{ color: item.color, transform: 'scale(1.5)' }}>
                {item.icon}
              </Box>
            </Box>
            <Typography
              variant="body2"
              sx={{
                fontWeight: 500,
                color: '#666666',
                textAlign: 'center',
              }}
            >
              {item.text}
            </Typography>
          </Paper>
        ))}
      </Box>
    </Container>
  );
};

export default QuickAccess; 