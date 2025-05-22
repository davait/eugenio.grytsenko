import React from 'react';
import {
  Box,
  Container,
  Grid,
  Typography,
  Link,
  Divider,
} from '@mui/material';

const Footer = () => {
  return (
    <Box
      component="footer"
      sx={{
        backgroundColor: '#FFFFFF',
        py: 6,
        mt: 'auto',
      }}
    >
      <Container maxWidth="lg">
        <Grid container spacing={4}>
          <Grid item xs={12} sm={4}>
            <Typography variant="h6" color="text.primary" gutterBottom>
              Acerca de
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Venta de Garage es tu plataforma para comprar y vender artículos usados
              de manera fácil y segura.
            </Typography>
          </Grid>
          <Grid item xs={12} sm={4}>
            <Typography variant="h6" color="text.primary" gutterBottom>
              Enlaces útiles
            </Typography>
            <Link href="#" color="inherit" display="block" sx={{ mb: 1 }}>
              Términos y condiciones
            </Link>
            <Link href="#" color="inherit" display="block" sx={{ mb: 1 }}>
              Política de privacidad
            </Link>
            <Link href="#" color="inherit" display="block" sx={{ mb: 1 }}>
              Ayuda
            </Link>
          </Grid>
          <Grid item xs={12} sm={4}>
            <Typography variant="h6" color="text.primary" gutterBottom>
              Contacto
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Email: contacto@ventadegarage.com
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Tel: (123) 456-7890
            </Typography>
          </Grid>
        </Grid>
        <Divider sx={{ my: 4 }} />
        <Typography variant="body2" color="text.secondary" align="center">
          © {new Date().getFullYear()} Venta de Garage. Todos los derechos reservados.
        </Typography>
      </Container>
    </Box>
  );
};

export default Footer; 