#include <WindHumanMouse>

MouseMoveHuman(X, Y){
    Random Speed, 0.45, 0.55
    MoveMouse(X, Y, Speed)
}

MouseClickHuman(X, Y){
    MouseMoveHuman(X, Y)
    MouseClick, L, %X%, %Y%
}

class MouseWindowNavigator {
	__New(origin_x, origin_y, window_width, window_height) {
		this.origin_x := origin_x
        this.origin_y := origin_y
        this.window_width := window_width
        this.window_height := window_height
	}
    MouseClickWindowHuman(x_window_ratio, y_window_ratio, x_range, y_range){
        ; TODO: perform bounds checking
        Random Xdev, -x_range, x_range
        Random Ydev, -y_range, y_range
        Xc := ((x_window_ratio + Xdev) * this.window_width) + this.origin_x
        Yc := ((y_window_ratio + Ydev) * this.window_height) + this.origin_y
        MouseClickHuman(Xc, Yc)
    }
}
