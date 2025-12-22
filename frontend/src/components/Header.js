import React from "react";
import { useNavigate, useLocation } from "react-router-dom";
import httpClient from "../components/httpClient";
import logo from "../assets/logo.jpg";
import "bootstrap/dist/js/bootstrap.min.js";

function Header({ user, setUser }) {
  const navigate = useNavigate();
  const location = useLocation();

  const logUserOut = async () => {
    await httpClient.post(`${process.env.REACT_APP_BACKEND_URL}/user/logout`);
    setUser(null);
    navigate("/");
  };

  return (
    <div>
      <nav className="navbar navbar-expand-sm bg-body-tertiary">
        <div className="d-flex flex-row justify-content-between mx-4 w-100">
          <div>
            <a className="navbar-brand me-2" href="/">
              <img src={logo} height="32" alt="Logo" />
            </a>

            <button className="navbar-toggler" type="button">
              <i className="fas fa-bars"></i>
            </button>
          </div>

          <div className="collapse navbar-collapse">
            {user !== null && user.role === "Administrateur" ? (
              <ul className="navbar-nav me-auto mb-2 mb-lg-0">
                <li className="nav-item">
                  <a className="nav-link" href="/admin/dashboard">{location.pathname.includes("dashboard") ? (<u>Admin</u>) : ("Admin")}</a>
                </li>
                <li className="nav-item">
                  <a className="nav-link" href="/liste-clients">{location.pathname.includes("client") ? <u>Clients</u> : "Clients"}</a>
                </li>
                <li className="nav-item">
                  <a className="nav-link" href="/liste-devis">{location.pathname.includes("devis") ? <u>Devis</u> : "Devis"}</a>
                </li>
                <li className="nav-item">
                  <a className="nav-link" href="/liste-articles">{location.pathname.includes("article") ? (<u>Articles</u>) : ("Articles")}</a>
                </li>
              </ul>
            ) : user !==null && user.role === "Utilisateur" ? (
              <ul className="navbar-nav me-auto mb-2 mb-lg-0">
                <li className="nav-item">
                  <a className="nav-link" href="/liste-clients">{location.pathname.includes("client") ? <u>Clients</u> : "Clients"}</a>
                </li>
                <li className="nav-item">
                  <a className="nav-link" href="/liste-devis">{location.pathname.includes("devis") ? <u>Devis</u> : "Devis"}</a>
                </li>
                <li className="nav-item">
                  <a className="nav-link" href="/liste-articles">{location.pathname.includes("article") ? (<u>Articles</u>) : ("Articles")}</a>
                </li>
              </ul>
            ) : (
              <ul className="navbar-nav mx-auto mb-2 mb-lg-0">
                <li className="nav-item"><h3>Connexion</h3>
                </li>
              </ul>
            )}

            {user !== null ? (
              <div className="d-flex align-items-center">
                <button type="button" onClick={logUserOut} className="btn btn-danger px-3 me-2">Se déconnecter</button>
              </div>
            ): null}
          </div>
        </div>
      </nav>
    </div>
  );
}

export default Header;
