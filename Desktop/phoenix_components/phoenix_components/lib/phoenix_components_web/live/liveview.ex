defmodule PhoenixComponentsWeb.CartLive.Index do
  use PhoenixComponentsWeb, :live_view
  alias PhoenixComponentsWeb.CartLive.ProductItem

  def mpunt(_params, _session, socket) do
    {:ok, assign(socket, total_itesms: 0)}
  end

  def handle_params(params, _, socket) do
    name = params["name"] || "guest"
    {:noreply, assign(socket, name: name, total_items: 0)}
  end

  def render(assigns) do
    ~H"""

    Hi <%= @name %> <%= self() |> :erlang.pid_to_list() %>

     <div class="w-full">
     <h2 class="text-2xl font-semibold mb-3">Shopping Cart - Total Items: <%= @total_items %></h2>
    <.live_component :for={id <- 1..3} module={ProductItem} id={id} />


    </div>
    """
  end


  def handle_info(:add, socket) do
    {:noreply, update(socket, :total_items, &(&1 + 1))}
  end
end
