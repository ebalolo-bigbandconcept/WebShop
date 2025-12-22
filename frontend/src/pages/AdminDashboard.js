import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import httpClient from "../components/httpClient";
import bootstrap from "bootstrap/dist/js/bootstrap.js";

function AdminDashboard() {
  const navigate = useNavigate();

  const [users, setUsers] = useState();
  const [new_prenom, setNewFirstName] = useState("");
  const [new_nom, setNewLastName] = useState("");
  const [new_email, setNewEmail] = useState("");
  const [new_password, setNewPassword] = useState("");
  const [new_role, setNewRole] = useState("Utilisateur");

  const [form_submited, setFormSubmited] = useState(false);
  const [first_name_error, setFirstNameError] = useState("");
  const [last_name_error, setLastNameError] = useState("");
  const [email_error, setEmailError] = useState("");
  const [password_error, setPasswordError] = useState("");

  // ### User input verifications ###
  const firstNameVerif = (value) => {
    if (value === "") {
      setFirstNameError("Veuillez entrer votre prénom");
      return false;
    }
    setFirstNameError("");
    return true;
  };

  const lastNameVerif = (value) => {
    if (value === "") {
      setLastNameError("Veuillez entrer votre nom");
      return false;
    }
    setLastNameError("");
    return true;
  };

  const emailVerif = (value) => {
    if (value === "") {
      setEmailError("Veuillez entrer votre email");
      return false;
    }
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(value)) {
      setEmailError("Format d'email invalide");
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
    const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[\W_]).{8,}$/;
    if (!passwordRegex.test(value)) {
      setPasswordError(
        "Le mot de passe doit contenir au moins 8 caractères et doit inclure une majuscule, une minuscule, un chiffre et un caractère spécial."
      );
      return false;
    }
    setPasswordError("");
    return true;
  };

  // ### Fetch all users from the backend ###
  const getAllUsersInfo = async () => {
    httpClient
      .get(`${process.env.REACT_APP_BACKEND_URL}/admin/all-user`)
      .then((resp) => {
        setUsers(resp.data);
      })
      .catch((error) => {
        if (error.response && error.response.data && error.response.data.error) {
          alert(error.response.data.error);
        } else {
          alert("Une erreur est survenue.");
        }
      });
  };

  // ### Add a new user to the database ###
  const addNewUser = async (e) => {
    e.preventDefault();
    setFormSubmited(true);

    const isFirstNameValid = firstNameVerif(new_prenom);
    const isLastNameValid = lastNameVerif(new_nom);
    const isEmailValid = emailVerif(new_email);
    const isPasswordValid = passwordVerif(new_password);

    const isFormValid =
      isFirstNameValid && isLastNameValid && isEmailValid && isPasswordValid;

    if (isFormValid) {
      httpClient
        .post(`${process.env.REACT_APP_BACKEND_URL}/admin/create-user`, {
          prenom: new_prenom,
          nom: new_nom,
          email: new_email,
          mdp: new_password,
          role: new_role,
        })
        .then((resp) => {
          console.log(resp);
          handleClose();
          getAllUsersInfo();
        })
        .catch((error) => {
          if (error.response && error.response.data && error.response.data.error) {
            if (error.response.status === 409){
              setEmailError(error.response.data.error)
            }else{
              alert(error.response.data.error);
            }
          } else {
            alert("Une erreur est survenue.");
          }
        });
    }
  };

  const handleClose = () => {
    // Close modal
    const popup = document.getElementById("popup");
    const modal = bootstrap.Modal.getInstance(popup);
    if (modal){
      modal.hide();
    }
    // Close modal residues
    const backdrops = document.querySelectorAll(".modal-backdrop");
    backdrops.forEach((b) => b.remove());

    document.body.classList.remove("modal-open");
    document.body.style.overflow = "";
    document.body.style.paddingRight = "";
    // Reset form
    setNewFirstName("");
    setNewLastName("");
    setNewEmail("");
    setNewPassword("");
    setNewRole("Utilisateur");
    setFormSubmited(false);
    setFirstNameError("");
    setLastNameError("");
    setEmailError("");
    setPasswordError("");
  };

  useEffect(() => {
    getAllUsersInfo();
  }, []);

  return (
    <div>
      <h1>Tableau de bord administrateur</h1>
      <div>
        <button className="btn btn-primary" data-bs-toggle="modal" data-bs-target="#popup">+ Ajouter un nouvel utilisateur</button>
        <button
          className="btn btn-outline-secondary ms-2"
          type="button"
          onClick={() => navigate("/admin/parameters")}
        >
          Parametres de l'application
        </button>
        <br />
        <br />
        <div className="modal fade" id="popup" tabIndex="-1" data-bs-backdrop="static" data-bs-keyboard="false">
          <div className="modal-dialog modal-xl">
            <div className="modal-content">
              <div className="modal-header">
                <h1 className="modal-title fs-5" id="popupLabel">Ajouter un nouvel utilisateur.</h1>
              </div>
              <div className="modal-body">
                <form className="row">
                  <div className="form-outline col-4">
                    <label className="form-label">Nom</label>
                    <input type="text" id="nom" value={new_nom} onChange={(e) => {setNewLastName(e.target.value);lastNameVerif(e.target.value);}}
                      className={`form-control form-control-lg ${last_name_error ? "is-invalid" : form_submited ? "is-valid": ""}`} placeholder="Entrer un nouveau nom"/>
                    <div className="invalid-feedback">{last_name_error}</div>
                  </div>
                  <div className="form-outline col-4">
                    <label className="form-label">Prénom</label>
                    <input type="text" id="prénom" value={new_prenom} onChange={(e) => {setNewFirstName(e.target.value);firstNameVerif(e.target.value);}}
                      className={`form-control form-control-lg ${first_name_error ? "is-invalid" : form_submited ? "is-valid" : ""}`} placeholder="Entrer un nouveau prénom"
                    />
                    <div className="invalid-feedback">{first_name_error}</div>
                  </div>
                  <div className="form-outline col-4">
                    <label className="form-label">Rôle</label>
                    <select className="form-select form-select-lg" onChange={(e) => setNewRole(e.target.value)}>
                      <option value="Utilisateur">Utilisateur</option>
                      <option value="Administrateur">Administrateur</option>
                    </select>
                  </div>
                  <div className="form-outline mt-4">
                    <label className="form-label">Adresse mail</label>
                    <input type="email" id="email" value={new_email} onChange={(e) => {setNewEmail(e.target.value);emailVerif(e.target.value);}}
                      className={`form-control form-control-lg ${email_error ? "is-invalid" : form_submited ? "is-valid" : ""}`}placeholder="Entrer une nouvelle adresse  mail"/>
                    <div className="invalid-feedback">{email_error}</div>
                  </div>
                  <div className="form-outline mt-4">
                    <label className="form-label">Mot de passe</label>
                    <input type="password" id="mdp" value={new_password} onChange={(e) => { setNewPassword(e.target.value); passwordVerif(e.target.value);}}
                      className={`form-control form-control-lg ${password_error ? "is-invalid" : form_submited ? "is-valid" : ""}`}placeholder="Entrer un nouveau mot de passe"/>
                    <div className="invalid-feedback">{password_error}</div>
                  </div>
                </form>
              </div>
              <div className="modal-footer d-flex justify-content-between">
                <button className="btn btn-lg btn-danger" data-bs-dismiss="modal" onClick={handleClose}>Annuler</button>
                <button className="btn btn-lg btn-success" onClick={addNewUser}>Enregistrer</button>
              </div>
            </div>
          </div>
        </div>
      </div>
      <table className="table table-hover table-striped">
        <thead>
          <tr>
            <th scope="col">#</th>
            <th scope="col">Nom</th>
            <th scope="col">Prénom</th>
            <th scope="col">Adresse mail</th>
            <th scope="col">Rôle</th>
          </tr>
        </thead>
        <tbody>
          {users !== undefined ? (
            users.data.map((user) => (
              <tr key={user.id} onClick={() => {
                navigate({ pathname: `/admin/manage-user/` + user.id });
              }}>
                <td>{user.id}</td>
                <td>{user.nom}</td>
                <td>{user.prenom}</td>
                <td>{user.email}</td>
                <td>{user.role}</td>
              </tr>
            ))
          ) : (
            <tr>
              <td>"Chargement..."</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

export default AdminDashboard;
