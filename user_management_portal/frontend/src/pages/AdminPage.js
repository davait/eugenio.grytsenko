import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  Paper,
  CircularProgress,
  Alert,
  Button,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
} from '@mui/material';
import { DataGridPro } from '@mui/x-data-grid-pro';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';
import axios from 'axios';
import UserModal from '../components/UserModal';

const AdminPage = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [isEditing, setIsEditing] = useState(false);

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/users');
      setUsers(response.data);
      setLoading(false);
    } catch (err) {
      setError('Error fetching users. Please try again later.');
      setLoading(false);
      console.error('Error fetching users:', err);
    }
  };

  const handleCreateUser = async (userData) => {
    try {
      await axios.post('http://localhost:8000/api/users', userData);
      setModalOpen(false);
      fetchUsers();
    } catch (err) {
      const errorMessage = err.response?.data?.detail || 
        (typeof err.response?.data === 'object' ? JSON.stringify(err.response.data) : 'Error creating user');
      setError(errorMessage);
      console.error('Error creating user:', err);
    }
  };

  const handleUpdateUser = async (userData) => {
    try {
      await axios.put(`http://localhost:8000/api/users/${selectedUser.id}`, userData);
      setModalOpen(false);
      setSelectedUser(null);
      fetchUsers();
    } catch (err) {
      const errorMessage = err.response?.data?.detail || 
        (typeof err.response?.data === 'object' ? JSON.stringify(err.response.data) : 'Error updating user');
      setError(errorMessage);
      console.error('Error updating user:', err);
    }
  };

  const handleDeleteUser = async () => {
    try {
      await axios.delete(`http://localhost:8000/api/users/${selectedUser.id}`);
      setDeleteDialogOpen(false);
      setSelectedUser(null);
      fetchUsers();
    } catch (err) {
      const errorMessage = err.response?.data?.detail || 
        (typeof err.response?.data === 'object' ? JSON.stringify(err.response.data) : 'Error deleting user');
      setError(errorMessage);
      console.error('Error deleting user:', err);
    }
  };

  const handleEditClick = (user) => {
    setSelectedUser(user);
    setIsEditing(true);
    setModalOpen(true);
  };

  const handleDeleteClick = (user) => {
    setSelectedUser(user);
    setDeleteDialogOpen(true);
  };

  const columns = [
    { field: 'id', headerName: 'ID', width: 70 },
    { field: 'username', headerName: 'Username', width: 130 },
    { field: 'email', headerName: 'Email', width: 200 },
    { field: 'full_name', headerName: 'Full Name', width: 200 },
    { field: 'department', headerName: 'Department', width: 130 },
    {
      field: 'created_at',
      headerName: 'Created At',
      width: 180,
      valueFormatter: (params) => {
        return new Date(params.value).toLocaleString();
      },
    },
    {
      field: 'actions',
      headerName: 'Actions',
      width: 120,
      sortable: false,
      renderCell: (params) => (
        <Box>
          <Tooltip title="Edit user">
            <IconButton
              onClick={() => handleEditClick(params.row)}
              size="small"
              color="primary"
            >
              <EditIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Delete user">
            <IconButton
              onClick={() => handleDeleteClick(params.row)}
              size="small"
              color="error"
            >
              <DeleteIcon />
            </IconButton>
          </Tooltip>
        </Box>
      ),
    },
  ];

  const initialState = {
    aggregation: {
      model: {
        department: 'group',
      },
    },
    columns: {
      columnVisibilityModel: {
        id: false,
      },
    },
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          User Management Dashboard
        </Typography>
        <Button
          variant="contained"
          color="primary"
          startIcon={<AddIcon />}
          onClick={() => {
            setIsEditing(false);
            setSelectedUser(null);
            setModalOpen(true);
          }}
        >
          Create User
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column' }}>
        <Box sx={{ height: 600, width: '100%' }}>
          <DataGridPro
            rows={users}
            columns={columns}
            initialState={initialState}
            groupingColDef={{
              headerName: 'Department',
              width: 200,
            }}
            disableRowSelectionOnClick
            experimentalFeatures={{
              columnGrouping: true,
            }}
          />
        </Box>
      </Paper>

      <UserModal
        open={modalOpen}
        handleClose={() => {
          setModalOpen(false);
          setSelectedUser(null);
        }}
        handleSubmit={isEditing ? handleUpdateUser : handleCreateUser}
        user={selectedUser}
        isEditing={isEditing}
      />

      <Dialog
        open={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
      >
        <DialogTitle>Confirm Delete</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete user {selectedUser?.username}? This action cannot be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleDeleteUser} color="error" variant="contained">
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default AdminPage; 