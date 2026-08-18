import { useAuth } from "../auth/AuthContext.jsx";

export default function ProfilePage() {
  const { currentUser } = useAuth();

  return (
    <section>
      <div className="page-heading">
        <p className="eyebrow">Profile</p>
        <h2>Your account</h2>
      </div>
      <section className="detail-panel">
        <dl>
          <div>
            <dt>Full name</dt>
            <dd>{currentUser.full_name}</dd>
          </div>
          <div>
            <dt>Email</dt>
            <dd>{currentUser.email}</dd>
          </div>
          <div>
            <dt>Role</dt>
            <dd>{currentUser.role}</dd>
          </div>
          <div>
            <dt>Account status</dt>
            <dd>{currentUser.account_status}</dd>
          </div>
        </dl>
      </section>
    </section>
  );
}

