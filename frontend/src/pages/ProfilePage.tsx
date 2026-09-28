import { PageHeader } from "../components/common/PageHeader";
import { ProfileForm } from "../components/profile/ProfileForm";

export function ProfilePage() {
  return (
    <div className="space-y-4">
      <PageHeader title="Profile" />
      <ProfileForm />
    </div>
  );
}
