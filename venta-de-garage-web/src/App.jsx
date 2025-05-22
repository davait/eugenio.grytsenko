import React, { useState } from 'react';
import { Box, CssBaseline } from '@mui/material';
import Header from './components/Header';
import Navbar from './components/Navbar';
import Banner from './components/Banner';
import QuickAccess from './components/QuickAccess';
import ProductGrid from './components/ProductGrid';
import Footer from './components/Footer';
import PublishModal from './components/PublishModal';
import Cart from './components/Cart';
import LoginModal from './components/LoginModal';
import RegisterModal from './components/RegisterModal';

function App() {
  const [isPublishModalOpen, setIsPublishModalOpen] = useState(false);
  const [isCartOpen, setIsCartOpen] = useState(false);
  const [isLoginModalOpen, setIsLoginModalOpen] = useState(false);
  const [isRegisterModalOpen, setIsRegisterModalOpen] = useState(false);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [originalSearchTerm, setOriginalSearchTerm] = useState('');
  const [suggestion, setSuggestion] = useState(null);
  const [locationFilter, setLocationFilter] = useState('');
  const [sellerIdFilter, setSellerIdFilter] = useState(null);

  const handlePublishClick = () => {
    setIsPublishModalOpen(true);
  };

  const handlePublishSuccess = () => {
    setRefreshTrigger(prev => prev + 1);
  };

  const handleSearch = (term, category, location = '', sellerId = null) => {
    setSearchTerm(location || (sellerId !== null && sellerId !== undefined) ? '' : term);
    setOriginalSearchTerm(term);
    setSelectedCategory(category);
    setSuggestion(null);
    setLocationFilter(location);
    setSellerIdFilter((sellerId !== null && sellerId !== undefined) ? Number(sellerId) : null);
  };

  const handleSuggestionFromGrid = (sugg) => {
    setSuggestion(sugg);
  };

  const handleSuggestionClick = (sugg) => {
    setSearchTerm(sugg);
    setSuggestion(null);
  };

  const handleOriginalSearchChange = (value) => {
    setOriginalSearchTerm(value);
  };

  const handleLoginClick = () => {
    setIsLoginModalOpen(true);
    setIsRegisterModalOpen(false);
  };

  const handleRegisterClick = () => {
    setIsRegisterModalOpen(true);
    setIsLoginModalOpen(false);
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <CssBaseline />
      
      <Header 
        onCartClick={() => setIsCartOpen(true)}
        onSearch={handleSearch}
        onOriginalSearchChange={handleOriginalSearchChange}
        suggestion={suggestion}
        onSuggestionClick={handleSuggestionClick}
        onLoginClick={handleLoginClick}
        onRegisterClick={handleRegisterClick}
      />
      
      <Navbar onPublishClick={handlePublishClick} />
      
      {!searchTerm && !selectedCategory && !locationFilter && sellerIdFilter === null && (
        <>
          <Banner onPublishClick={handlePublishClick} />
          <QuickAccess />
        </>
      )}
      
      <Box sx={{ flex: 1, pb: { xs: 6, sm: 8 } }}>
        <ProductGrid 
          refreshTrigger={refreshTrigger}
          searchTerm={searchTerm}
          category={selectedCategory}
          originalSearchTerm={originalSearchTerm}
          suggestion={suggestion}
          onSuggestionClick={handleSuggestionClick}
          onSuggestion={handleSuggestionFromGrid}
          locationFilter={locationFilter}
          sellerIdFilter={sellerIdFilter}
        />
      </Box>
      
      <Footer />
      
      <PublishModal
        open={isPublishModalOpen}
        onClose={() => setIsPublishModalOpen(false)}
        onPublished={handlePublishSuccess}
      />
      
      <Cart
        open={isCartOpen}
        onClose={() => setIsCartOpen(false)}
      />

      <LoginModal
        open={isLoginModalOpen}
        onClose={() => setIsLoginModalOpen(false)}
        onRegisterClick={handleRegisterClick}
      />

      <RegisterModal
        open={isRegisterModalOpen}
        onClose={() => setIsRegisterModalOpen(false)}
        onLoginClick={handleLoginClick}
      />
    </Box>
  );
}

export default App;
