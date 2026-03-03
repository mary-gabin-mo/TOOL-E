from kivymd.uix.screen import MDScreen

class BaseScreen(MDScreen):
    """
    Parent class for all screens.
    Includes helper methods for navigation.
    """
    
    def go_to(self, screen_name):
        """Forward navigation (Slide Left)"""
        # 'self.manager' is automatically available in all Screens
        if self.manager:
            self.manager.transition.direction = 'left'
            self.manager.current = screen_name 
            
    def go_back(self, screen_name):
        """Backward navigation (Slide Right)"""   
        if self.manager:
            self.manager.transition.direction = 'right'
            self.manager.current = screen_name
