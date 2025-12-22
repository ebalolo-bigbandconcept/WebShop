import { useState } from "react";
import { useNavigate } from "react-router-dom";
import httpClient from "../components/httpClient";
import { useToast } from "../components/Toast";

function Login({ setUser }) {
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [mdp, setPassword] = useState("");

  const [form_submited, setFormSubmited] = useState(false);
  const [email_error, setEmailError] = useState("");
  const [password_error, setPasswordError] = useState("");

  const { showToast } = useToast();

  // ### User input verifications ###
  const emailVerif = (value) => {
    if (value === "") {
      setEmailError("Veuillez entrer votre email");
      return false;
    }
    setEmailError("");
    return true;
  };

  const passwordVerif = (value) => {
    if (value === "") {
      setPasswordError("Veuillez entrer votre mot de passe");
      return false;
    }
    setPasswordError("");
    return true;
  };

  // ### Log user in ###
  const logUserIn = async () => {
    setFormSubmited(true);

    const isEmailValid = emailVerif(email);
    const isPasswordValid = passwordVerif(mdp);

    const isFormValid = isEmailValid && isPasswordValid;

    if (isFormValid){
      await httpClient.post(`${process.env.REACT_APP_BACKEND_URL}/user/login`, {
        email: email,
        mdp: mdp,
      })
      .then(function (response) {
        setUser(response.data);
        console.log("Connexion réussie.");
        navigate("/liste-clients");
      })
      .catch((error) => {
        if (error.response && error.response.data && error.response.data.error) {
          if (error.response.data.error === "Email invalide") {
            setEmailError("Email invalide");
          }if(error.response.data.error === "Mot de passe invalide"){
            setPasswordError("Mot de passe invalide");
          }
        } else {
          showToast({ message: "Une erreur est survenue.", variant: "danger" });
        }
      });
    }
  };

  return (
    <div className="vh-100 d-flex justify-content-center align-items-center">
      <div className="row d-flex justify-content-center align-items-center h-100">
        <div className="col-md-9 col-lg-6 col-xl-5">
          <img src="https://mdbcdn.b-cdn.net/img/Photos/new-templates/bootstrap-login-form/draw2.webp" className="img-fluid" alt="Sample"/>
        </div>
        <div className="col-md-8 col-lg-6 col-xl-4 offset-xl-1">
          <form>
            <div data-mdb-input-init className="form-outline mb-4">
              <label className="form-label">Adresse mail</label>
              <input type="email" id="email" value={email} onChange={(e) => {setEmail(e.target.value);emailVerif(e.target.value)}}
              className={`form-control form-control-lg ${email_error ? "is-invalid" : form_submited ? "is-valid" : ""}`} placeholder="Entrer une adresse mail valide"/>
              <div className="invalid-feedback">{email_error}</div>
            </div>

            <div data-mdb-input-init className="form-outline mb-3">
              <label className="form-label">Mot de passe</label>
              <input type="password" id="mdp" value={mdp} onChange={(e) => {setPassword(e.target.value);passwordVerif(e.target.value)}} 
              className={`form-control form-control-lg ${password_error ? "is-invalid" : form_submited ? "is-valid" : ""}`} placeholder="Entrer un mot de passe valide"/>
              <div className="invalid-feedback">{password_error}</div>
            </div>

            <div className="text-center text-lg-start mt-4 pt-2">
              <button type="button" onClick={logUserIn} data-mdb-button-init data-mdb-ripple-init className="btn btn-primary btn-lg">Se connecter</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

export default Login;
