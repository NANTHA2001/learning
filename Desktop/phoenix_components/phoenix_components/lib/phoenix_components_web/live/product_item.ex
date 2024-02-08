defmodule PhoenixComponentsWeb.CartLive.ProductItem do
  use PhoenixComponentsWeb, :live_component


  def update(assigns, socket) do
    socket =
    socket
    |> assign(assigns)
    |> assign(amount: 0)
    {:ok, socket}
  end


  def render(assigns) do
    ~H"""
    <div class="flex items-center justify-between mb-4">
    <span class="font-medium">product Name <%= @id %> </span>
    <span> <%= @amount %></span>
    <button phx-click="add" phx-target={@myself} class="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600">+ </button>
    </div>
    """
  end


  def handle_event("add", _, socket) do
    send self(), :add
    {:noreply, update(socket, :amount, &(&1 + 1))}
  end
end
