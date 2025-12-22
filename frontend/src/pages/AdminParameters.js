import { useEffect, useState } from "react";
import httpClient from "../components/httpClient";

function AdminParameters() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [parameters, setParameters] = useState({
    marginRate: "",
    marginRateLocation: "",
    locationTime: "",
    locationSubscriptionCost: "",
    locationInterestsCost: "",
    generalConditionsSales: "",
  });

  // Fetch existing parameters when the page loads
  useEffect(() => {
    let isMounted = true;

    const fetchParameters = async () => {
      try {
        const resp = await httpClient.get(
          `${process.env.REACT_APP_BACKEND_URL}/admin/parameters`
        );
        if (!isMounted) return;
        setParameters({
          marginRate: resp.data?.marginRate ?? "",
          marginRateLocation: resp.data?.marginRateLocation ?? "",
          locationTime: resp.data?.locationTime ?? "",
          locationSubscriptionCost: resp.data?.locationSubscriptionCost ?? "",
          locationInterestsCost: resp.data?.locationInterestsCost ?? "",
          generalConditionsSales: resp.data?.generalConditionsSales ?? "",
        });
      } catch (err) {
        if (!isMounted) return;
        console.error("Erreur lors du chargement des parametres", err);
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    fetchParameters();
    return () => {
      isMounted = false;
    };
  }, []);

  const handleChange = (key) => (e) => {
    setParameters((prev) => ({ ...prev, [key]: e.target.value }));
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setErrorMessage("");
    try {
      await httpClient.post(
        `${process.env.REACT_APP_BACKEND_URL}/admin/parameters`,
        parameters
      );
      alert("Parametres mis a jour");
    } catch (err) {
      const message = err.response?.data?.error ?? "Une erreur est survenue.";
      setErrorMessage(message);
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div>Chargement...</div>;

  return (
    <div>
      <h1>Parametres de l'application</h1>
      <p className="text-muted">
        Ajustez les valeurs globales appliquees aux devis et produits.
      </p>
      {errorMessage && (
        <div className="alert alert-danger" role="alert">
          {errorMessage}
        </div>
      )}
      <form className="row g-3" onSubmit={handleSave}>
        <div className="col-md-6">
          <label className="form-label">Taux de marge (x Prix de vente)</label>
          <input
            type="number"
            className="form-control"
            value={parameters.marginRate}
            onChange={handleChange("marginRate")}
            min="0"
            step="0.1"
          />
        </div>
        <div className="col-md-6">
          <label className="form-label">Taux de marge de location (x Prix de vente)</label>
          <input
            type="number"
            className="form-control"
            value={parameters.marginRateLocation}
            onChange={handleChange("marginRateLocation")}
            min="0"
            step="0.1"
          />
        </div>
        <div className="col-md-4">
          <label className="form-label">Temps de location (mois)</label>
          <input
            type="number"
            className="form-control"
            value={parameters.locationTime}
            onChange={handleChange("locationTime")}
            min="0"
            step="1"
          />
        </div>
        <div className="col-md-4">
          <label className="form-label">Coût d'abonement de location (EUR)</label>
          <input
            type="number"
            className="form-control"
            value={parameters.locationSubscriptionCost}
            onChange={handleChange("locationSubscriptionCost")}
            min="0"
            step="0.1"
          />
        </div>
        <div className="col-md-4">
          <label className="form-label">Intérêts de la location (EUR)</label>
          <input
            type="number"
            className="form-control"
            value={parameters.locationInterestsCost}
            onChange={handleChange("locationInterestsCost")}
            min="0"
            step="0.1"
          />
        </div>
        <div className="col-12">
          <label className="form-label">Conditions générales de vente</label>
          <textarea
            className="form-control"
            value={parameters.generalConditionsSales}
            onChange={handleChange("generalConditionsSales")}
            rows="6"
          ></textarea>
        </div>
        <div className="col-12 d-flex justify-content-end gap-2">
          <button
            type="button"
            className="btn btn-outline-secondary"
            onClick={() => window.history.back()}
            disabled={saving}
          >
            Retour
          </button>
          <button type="submit" className="btn btn-primary" disabled={saving}>
            {saving ? "Enregistrement..." : "Enregistrer"}
          </button>
        </div>
      </form>
    </div>
  );
}

export default AdminParameters;
