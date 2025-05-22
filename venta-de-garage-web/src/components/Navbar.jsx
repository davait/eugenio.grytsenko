import React from 'react';
import { Box, Button, Container } from '@mui/material';
import {
  Category as CategoryIcon,
  LocalOffer as OfferIcon,
  Favorite as FavoriteIcon,
  Help as HelpIcon,
  Store as StoreIcon,
} from '@mui/icons-material';

const navItems = [
  { text: 'Categorías', icon: <CategoryIcon /> },
  { text: 'Ofertas', icon: <OfferIcon /> },
  { text: 'Favoritos', icon: <FavoriteIcon /> },
  { text: 'Ayuda', icon: <HelpIcon /> },
  { text: 'Publicar', icon: <StoreIcon /> },
];

const Navbar = ({ onPublishClick }) => {
  return (
    <Box
      sx={{
        backgroundColor: '#FFF159',
        py: 1,
        boxShadow: '0 1px 3px rgba(0,0,0,0.12)',
      }}
    >
      <Container>
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'flex-start',
            gap: 2,
            overflowX: 'auto',
          }}
        >
          {navItems.map((item, index) => (
            <Button
              key={index}
              startIcon={item.icon}
              onClick={item.text === 'Publicar' ? onPublishClick : undefined}
              sx={{
                color: '#333333',
                textTransform: 'none',
                '&:hover': {
                  backgroundColor: 'rgba(0,0,0,0.04)',
                },
                whiteSpace: 'nowrap',
              }}
            >
              {item.text}
            </Button>
          ))}
        </Box>
      </Container>
    </Box>
  );
};

export default Navbar; 