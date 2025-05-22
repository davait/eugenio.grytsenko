import React from 'react';
import { Box, Container, Typography, Button } from '@mui/material';

const Banner = ({ onPublishClick }) => {
  return (
    <Box
      sx={{
        background: 'linear-gradient(45deg, #FFE600 30%, #FFF159 90%)',
        py: 6,
        mb: 4,
      }}
    >
      <Container>
        <Box
          sx={{
            display: 'flex',
            flexDirection: { xs: 'column', md: 'row' },
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 4,
          }}
        >
          <Box sx={{ flex: 1, textAlign: { xs: 'center', md: 'left' } }}>
            <Typography
              variant="h3"
              component="h1"
              sx={{
                color: '#333333',
                fontWeight: 'bold',
                mb: 2,
              }}
            >
              ¡VENTA DE GARAGE!
            </Typography>
            <Typography
              variant="h5"
              sx={{
                color: '#666666',
                mb: 3,
              }}
            >
              Vendé lo que ya no usás y ganá dinero extra
            </Typography>
            <Button
              variant="contained"
              size="large"
              onClick={onPublishClick}
              sx={{
                backgroundColor: '#3483FA',
                color: 'white',
                fontWeight: 'bold',
                '&:hover': {
                  backgroundColor: '#2968c8',
                },
                px: 4,
                py: 1.5,
              }}
            >
              VENDÉ O DONÁ TUS COSAS
            </Button>
          </Box>
          <Box
            sx={{
              flex: 1,
              display: 'flex',
              justifyContent: 'center',
            }}
          >
            <img
              src="http://localhost:8000/static/banner.jpg"
              alt="Venta de Garage"
              style={{
                maxWidth: '100%',
                height: 'auto',
                borderRadius: '8px',
                boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
              }}
            />
          </Box>
        </Box>
      </Container>
    </Box>
  );
};

export default Banner; 