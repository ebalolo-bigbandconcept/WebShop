import { useEffect, useState, lazy, Suspense } from "react";
import { BrowserRouter, Routes, Route, useNavigate } from 'react-router-dom'
import httpClient from "./components/httpClient";
import './App.css';

// Component imports
const Header = lazy(() => import('./components/Header'));
const Footer = lazy(() => import('./components/Footer'));
const PrivateRoute = lazy(() => import ('./components/PrivateRoute'));

// Page imports
const Login = lazy(() => import ('./pages/Login'));
const NotFound = lazy(() => import ('./pages/NotFound'));
const AdminDashboard = lazy(() => import ('./pages/AdminDashboard'));
const ManageUser = lazy(() => import ('./pages/AdminManageUser'));
const ListeClients = lazy(() => import ('./pages/ListeClients'));
const Client = lazy(() => import ('./pages/Client'));
const ListeArticles = lazy(() => import ('./pages/AdminListeArticles'));
const ListeDevis = lazy(() => import ('./pages/ListeDevis'));
const Devis = lazy(() => import ('./pages/Devis'));
const DevisPdf = lazy(() => import ('./pages/DevisPdf'));
const ConsentComplete = lazy(() => import ('./pages/ConsentComplete'));

function App() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // ### Fetch the current user on app load ###
  useEffect(() => {
    let isMounted = true;

    const fetchUser = async () => {
      try {
        const resp = await httpClient.get(`${process.env.REACT_APP_BACKEND_URL}/user/me`);
        if (isMounted) setUser(resp.data);
      } catch (error) {
        if (error.response && error.response.data.error === "Unauthorized") {
          console.log("No user logged in.");
          navigate("/");
        }else{
          console.error("Error fetching user:", error);
        }
        if (isMounted) setUser(null);
      } finally {
        if (isMounted) setLoading(false);
      }
    };
    
    fetchUser();
    return () => { isMounted = false; };
  }, []);

  if (loading) return <div>Chargement...</div>;

  return (
    <div className="d-flex flex-column min-vh-100">
      <Header user={user} setUser={setUser}/>
      <div className='container mt-4 min-vh-100'>
        <Suspense fallback={<div>Chargement...</div>}>
          <Routes>
            <Route path="/" element={<Login setUser={setUser}/>}/>
            <Route path="/*" element={<NotFound/>}/>
            <Route path="/consent_complete" element={
              <PrivateRoute user={user} requiredRole={['Administrateur']}>
                <ConsentComplete/>
              </PrivateRoute>
            }/>
            <Route path="/liste-clients" element={
              <PrivateRoute user={user} requiredRole={['Administrateur', 'Utilisateur']}>
                <ListeClients/>
              </PrivateRoute>
            }/>
            <Route path="/client/:id" element={
              <PrivateRoute user={user} requiredRole={['Administrateur', 'Utilisateur']}>
                <Client/>
              </PrivateRoute>
            }/>
            <Route path="/liste-devis" element={
              <PrivateRoute user={user} requiredRole={['Administrateur', 'Utilisateur']}>
                <ListeDevis/>
              </PrivateRoute>
            }/>
            <Route path="/devis/:id_client/:id_devis" element={
              <PrivateRoute user={user} requiredRole={['Administrateur', 'Utilisateur']}>
                <Devis/>
              </PrivateRoute>
            }/>
            <Route path="/devis/:id_client/:id_devis/pdf" element={
              <PrivateRoute user={user} requiredRole={['Administrateur', 'Utilisateur']}>
                <DevisPdf/>
              </PrivateRoute>
            }/>
            <Route path="/liste-articles" element={
              <PrivateRoute user={user} requiredRole={['Administrateur', 'Utilisateur']}>
                <ListeArticles/>
              </PrivateRoute>
            }/>
            <Route path="/admin/dashboard" element={
              <PrivateRoute user={user} requiredRole={'Administrateur'}>
                <AdminDashboard setUser={setUser}/>
              </PrivateRoute>
            }/>
            <Route path="/admin/liste-articles" element={
              <PrivateRoute user={user} requiredRole={['Administrateur', 'Utilisateur']}>
                <ListeArticles/>
              </PrivateRoute>
            }/>
            <Route path="/admin/manage-user/:id" element={
              <PrivateRoute user={user} requiredRole={'Administrateur'}>
                <ManageUser/>
              </PrivateRoute>
            }/>
          </Routes>
        </Suspense>
      </div>
      <Footer />
    </div>
  );
}

const AppWrapper = () => (
  <BrowserRouter>
    <App />
  </BrowserRouter>
);

export default AppWrapper;