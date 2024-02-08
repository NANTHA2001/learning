defmodule PhoenixComponents.Repo do
  use Ecto.Repo,
    otp_app: :phoenix_components,
    adapter: Ecto.Adapters.Postgres
end
