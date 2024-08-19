## Gnome App
This is a prototype `fluxnote` client for Gnome so that Linux users have a GUI. It is written in Swift and uses the `adwaita-swift` library for the UI. It is a work in progress and is not yet functional and may well take a back seat to the macOS client.

## Notes
Getting the app to build on Arch was quite simple after installing GNOME Builder and the dependencies it suggested. Ubuntu was much more challenging and so that is what the flatpak script is for. It requires flatpak-builder and flatpak to be installed, which can be done with `sudo apt install flatpak-builder flatpak`. 

## TODO
- [ ] Copy the websocket manager over from the macOS client as they are both in Swift.
- [ ] Implement everything else.
