import React, { useState, useEffect } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import axios from "axios";
import { Button } from "./components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./components/ui/card";
import { Badge } from "./components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import { Input } from "./components/ui/input";
import { Label } from "./components/ui/label";
import { Textarea } from "./components/ui/textarea";
import { Alert, AlertDescription } from "./components/ui/alert";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "./components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./components/ui/select";
import { Separator } from "./components/ui/separator";
import { useToast } from "./hooks/use-toast";
import { Toaster } from "./components/ui/toaster";
import { 
  Home, 
  User, 
  ShoppingCart, 
  FileText, 
  Shield, 
  LogIn, 
  UserPlus, 
  Coins, 
  AlertTriangle,
  Settings,
  TrendingUp,
  Users,
  Activity,
  Bell,
  Edit,
  ToggleLeft,
  ToggleRight,
  Image,
  Menu,
  X,
  Search,
  Filter,
  SortAsc,
  SortDesc,
  ChevronLeft,
  ChevronRight,
  Download,
  Star
} from "lucide-react";

// Import Recharts components
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  Area,
  AreaChart
} from 'recharts';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = React.createContext(null);

const useAuth = () => {
  const context = React.useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      fetchProfile();
    } else {
      setIsLoading(false);
    }
  }, [token]);

  const fetchProfile = async () => {
    try {
      const response = await axios.get(`${API}/profile`);
      setUser(response.data);
    } catch (error) {
      console.error('Failed to fetch profile:', error);
      logout();
    } finally {
      setIsLoading(false);
    }
  };

  const login = (newToken, userData) => {
    localStorage.setItem('token', newToken);
    setToken(newToken);
    setUser(userData);
    setIsLoading(false);
    axios.defaults.headers.common['Authorization'] = `Bearer ${newToken}`;
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    setIsLoading(false);
    delete axios.defaults.headers.common['Authorization'];
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, isAuthenticated: !!user && !!token, isLoading }}>
      {children}
    </AuthContext.Provider>
  );
};

// Navigation Component
const Navigation = () => {
  const { user, logout, isAuthenticated } = useAuth();
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  useEffect(() => {
    if (isAuthenticated) {
      fetchNotifications();
    }
  }, [isAuthenticated]);

  const fetchNotifications = async () => {
    try {
      const response = await axios.get(`${API}/notifications`);
      const notifs = response.data || [];
      setNotifications(notifs);
      setUnreadCount(notifs.filter(n => !n.is_read).length);
    } catch (error) {
      console.error('Failed to fetch notifications:', error);
    }
  };

  const markAsRead = async (notificationId) => {
    try {
      await axios.post(`${API}/notifications/${notificationId}/read`);
      fetchNotifications();
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
    }
  };

  return (
    <nav className="bg-gradient-to-r from-blue-900 via-purple-900 to-pink-900 text-white shadow-2xl">
      {/* Desktop Navigation */}
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex justify-between items-center py-4">
          {/* Logo */}
          <div className="flex items-center space-x-3">
            <div className="bg-white/20 p-2 rounded-full">
              <Activity className="h-8 w-8 text-white" />
            </div>
            <h1 className="text-2xl font-bold bg-gradient-to-r from-white to-blue-200 bg-clip-text text-transparent">
              SwagMedia
            </h1>
          </div>
          
          {/* Desktop Menu */}
          <div className="hidden lg:flex items-center space-x-8">
            <a href="/" className="hover:text-blue-200 flex items-center space-x-2 transition-all duration-200 hover:scale-105">
              <Home className="h-4 w-4" />
              <span>Главная</span>
            </a>
            
            <a href="/media-list" className="hover:text-blue-200 flex items-center space-x-2 transition-all duration-200 hover:scale-105">
              <Users className="h-4 w-4" />
              <span>Медиа</span>
            </a>

            <a href="/ratings" className="hover:text-blue-200 flex items-center space-x-2 transition-all duration-200 hover:scale-105">
              <Star className="h-4 w-4" />
              <span>Рейтинги</span>
            </a>

            {isAuthenticated && (
              <>
                <a href="/profile" className="hover:text-blue-200 flex items-center space-x-2 transition-all duration-200 hover:scale-105">
                  <User className="h-4 w-4" />
                  <span>Профиль</span>
                </a>
                
                <a href="/shop" className="hover:text-blue-200 flex items-center space-x-2 transition-all duration-200 hover:scale-105">
                  <ShoppingCart className="h-4 w-4" />
                  <span>Магазин</span>
                </a>
                
                <a href="/reports" className="hover:text-blue-200 flex items-center space-x-2 transition-all duration-200 hover:scale-105">
                  <FileText className="h-4 w-4" />
                  <span>Отчеты</span>
                </a>

                {user?.admin_level >= 1 && (
                  <a href="/admin" className="hover:text-blue-200 flex items-center space-x-2 transition-all duration-200 hover:scale-105">
                    <Shield className="h-4 w-4" />
                    <span>Админ</span>
                  </a>
                )}
              </>
            )}
          </div>

          {/* Right Side - Notifications, Balance, Auth */}
          <div className="flex items-center space-x-2 lg:space-x-4">
            {isAuthenticated && (
              <>
                {/* Notifications */}
                <Dialog>
                  <DialogTrigger asChild>
                    <Button variant="ghost" size="sm" className="hover:bg-white/20 transition-all duration-200 relative">
                      <Bell className="h-4 w-4" />
                      {unreadCount > 0 && (
                        <Badge className="absolute -top-1 -right-1 h-5 w-5 p-0 flex items-center justify-center bg-red-500 text-white text-xs">
                          {unreadCount}
                        </Badge>
                      )}
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="max-w-md">
                    <DialogHeader>
                      <DialogTitle>Уведомления</DialogTitle>
                      <DialogDescription>
                        У вас {notifications.length} уведомлений
                      </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-2 max-h-96 overflow-y-auto">
                      {notifications.length === 0 ? (
                        <div className="text-center text-gray-500 py-4">
                          <Bell className="h-8 w-8 mx-auto mb-2 text-gray-400" />
                          <p>Нет уведомлений</p>
                        </div>
                      ) : (
                        notifications.map((notification) => (
                          <div 
                            key={notification.id} 
                            className={`p-3 rounded-lg border cursor-pointer transition-all ${
                              notification.is_read ? 'bg-gray-50 border-gray-200' : 'bg-blue-50 border-blue-200'
                            }`}
                            onClick={() => {
                              if (!notification.is_read) {
                                markAsRead(notification.id);
                              }
                            }}
                          >
                            <div className="flex justify-between items-start mb-1">
                              <span className="font-semibold text-sm">{notification.type}</span>
                              {!notification.is_read && (
                                <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                              )}
                            </div>
                            <p className="text-sm text-gray-700">{notification.message}</p>
                            <p className="text-xs text-gray-500 mt-1">
                              {new Date(notification.created_at).toLocaleString('ru-RU')}
                            </p>
                          </div>
                        ))
                      )}
                    </div>
                  </DialogContent>
                </Dialog>

                {/* Balance - Hidden on small screens */}
                <div className="hidden sm:flex bg-white/20 rounded-full px-3 py-2 items-center space-x-2">
                  <Coins className="h-4 w-4 text-yellow-400" />
                  <span className="text-yellow-400 font-semibold text-sm">
                    {user?.balance?.toLocaleString() || 0} MC
                  </span>
                </div>

                {/* Logout - Hidden on mobile */}
                <Button 
                  variant="ghost" 
                  size="sm" 
                  onClick={logout} 
                  className="hidden sm:block hover:bg-white/20 transition-all duration-200"
                >
                  Выйти
                </Button>
              </>
            )}

            {!isAuthenticated && (
              <div className="hidden sm:flex space-x-3">
                <Button variant="ghost" size="sm" className="hover:bg-white/20 transition-all duration-200" asChild>
                  <a href="/login">Войти</a>
                </Button>
                <Button variant="outline" size="sm" className="bg-white/20 border-white/30 hover:bg-white/30 transition-all duration-200" asChild>
                  <a href="/register">Регистрация</a>
                </Button>
              </div>
            )}

            {/* Mobile Menu Button */}
            <Button
              variant="ghost"
              size="sm"
              className="lg:hidden hover:bg-white/20 transition-all duration-200"
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            >
              {isMobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </Button>
          </div>
        </div>
      </div>

      {/* Mobile Menu */}
      {isMobileMenuOpen && (
        <div className="lg:hidden bg-black/20 backdrop-blur-sm border-t border-white/20">
          <div className="max-w-7xl mx-auto px-4 py-4 space-y-3">
            {/* Navigation Links */}
            <a 
              href="/" 
              className="flex items-center space-x-3 py-2 px-3 rounded-lg hover:bg-white/10 transition-all"
              onClick={() => setIsMobileMenuOpen(false)}
            >
              <Home className="h-5 w-5" />
              <span>Главная</span>
            </a>
            
            <a 
              href="/media-list" 
              className="flex items-center space-x-3 py-2 px-3 rounded-lg hover:bg-white/10 transition-all"
              onClick={() => setIsMobileMenuOpen(false)}
            >
              <Users className="h-5 w-5" />
              <span>Медиа</span>
            </a>

            <a 
              href="/ratings" 
              className="flex items-center space-x-3 py-2 px-3 rounded-lg hover:bg-white/10 transition-all"
              onClick={() => setIsMobileMenuOpen(false)}
            >
              <Star className="h-5 w-5" />
              <span>Рейтинги</span>
            </a>

            {isAuthenticated && (
              <>
                {/* Balance on Mobile */}
                <div className="flex items-center space-x-3 py-2 px-3 bg-white/10 rounded-lg">
                  <Coins className="h-5 w-5 text-yellow-400" />
                  <span className="text-yellow-400 font-semibold">Баланс: {user?.balance?.toLocaleString() || 0} MC</span>
                </div>

                <a 
                  href="/profile" 
                  className="flex items-center space-x-3 py-2 px-3 rounded-lg hover:bg-white/10 transition-all"
                  onClick={() => setIsMobileMenuOpen(false)}
                >
                  <User className="h-5 w-5" />
                  <span>Профиль</span>
                </a>
                
                <a 
                  href="/shop" 
                  className="flex items-center space-x-3 py-2 px-3 rounded-lg hover:bg-white/10 transition-all"
                  onClick={() => setIsMobileMenuOpen(false)}
                >
                  <ShoppingCart className="h-5 w-5" />
                  <span>Магазин</span>
                </a>
                
                <a 
                  href="/reports" 
                  className="flex items-center space-x-3 py-2 px-3 rounded-lg hover:bg-white/10 transition-all"
                  onClick={() => setIsMobileMenuOpen(false)}
                >
                  <FileText className="h-5 w-5" />
                  <span>Отчеты</span>
                </a>

                {user?.admin_level >= 1 && (
                  <a 
                    href="/admin" 
                    className="flex items-center space-x-3 py-2 px-3 rounded-lg hover:bg-white/10 transition-all"
                    onClick={() => setIsMobileMenuOpen(false)}
                  >
                    <Shield className="h-5 w-5" />
                    <span>Админ панель</span>
                  </a>
                )}

                <div className="border-t border-white/20 pt-3">
                  <Button 
                    variant="ghost" 
                    size="sm" 
                    onClick={() => {
                      logout();
                      setIsMobileMenuOpen(false);
                    }}
                    className="w-full justify-start hover:bg-white/10 transition-all duration-200"
                  >
                    <LogIn className="h-5 w-5 mr-3" />
                    Выйти
                  </Button>
                </div>
              </>
            )}

            {!isAuthenticated && (
              <div className="space-y-2 border-t border-white/20 pt-3">
                <Button 
                  variant="ghost" 
                  size="sm" 
                  className="w-full justify-start hover:bg-white/10 transition-all duration-200" 
                  asChild
                >
                  <a href="/login" onClick={() => setIsMobileMenuOpen(false)}>
                    <LogIn className="h-5 w-5 mr-3" />
                    Войти
                  </a>
                </Button>
                <Button 
                  variant="outline" 
                  size="sm" 
                  className="w-full justify-start bg-white/20 border-white/30 hover:bg-white/30 transition-all duration-200" 
                  asChild
                >
                  <a href="/register" onClick={() => setIsMobileMenuOpen(false)}>
                    <UserPlus className="h-5 w-5 mr-3" />
                    Регистрация
                  </a>
                </Button>
              </div>
            )}
          </div>
        </div>
      )}
    </nav>
  );
};

// Home Page
const HomePage = () => {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API}/stats`);
      setStats(response.data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50">
      <div className="max-w-7xl mx-auto px-4 py-12">
        <div className="text-center mb-16">
          <h1 className="text-6xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 mb-6 animate-pulse">
            Добро пожаловать в SwagMedia
          </h1>
          <p className="text-xl text-gray-600 max-w-4xl mx-auto leading-relaxed">
            🎯 Платформа для медиа-создателей с собственной экономикой и системой вознаграждений
          </p>
          <div className="mt-8 flex justify-center space-x-4">
            <div className="bg-white rounded-full px-6 py-2 shadow-lg">
              <span className="text-blue-600 font-semibold">💎 Медиа-коины</span>
            </div>
            <div className="bg-white rounded-full px-6 py-2 shadow-lg">
              <span className="text-purple-600 font-semibold">🚀 Премиум контент</span>
            </div>
            <div className="bg-white rounded-full px-6 py-2 shadow-lg">
              <span className="text-pink-600 font-semibold">⭐ Эксклюзивные товары</span>
            </div>
          </div>
        </div>

        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-16">
            <Card className="text-center hover:shadow-xl transition-all duration-300 hover:scale-105 bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
              <CardHeader>
                <CardTitle className="flex items-center justify-center space-x-2 text-blue-700">
                  <Users className="h-8 w-8" />
                  <span className="text-lg">Медиа участников</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-4xl font-bold text-blue-600 mb-2">{stats.total_media}</div>
                <p className="text-blue-600/80">Активных создателей контента</p>
              </CardContent>
            </Card>

            <Card className="text-center hover:shadow-xl transition-all duration-300 hover:scale-105 bg-gradient-to-br from-green-50 to-green-100 border-green-200">
              <CardHeader>
                <CardTitle className="flex items-center justify-center space-x-2 text-green-700">
                  <TrendingUp className="h-8 w-8" />
                  <span className="text-lg">Потрачено MC</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-4xl font-bold text-green-600 mb-2">{stats.total_mc_spent.toLocaleString()}</div>
                <p className="text-green-600/80">Медиа-коинов в магазине</p>
              </CardContent>
            </Card>

            <Card className="text-center hover:shadow-xl transition-all duration-300 hover:scale-105 bg-gradient-to-br from-yellow-50 to-yellow-100 border-yellow-200">
              <CardHeader>
                <CardTitle className="flex items-center justify-center space-x-2 text-yellow-700">
                  <Coins className="h-8 w-8" />
                  <span className="text-lg">Активных MC</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-4xl font-bold text-yellow-600 mb-2">{stats.total_mc_current.toLocaleString()}</div>
                <p className="text-yellow-600/80">В обращении сейчас</p>
              </CardContent>
            </Card>
          </div>
        )}

        <div className="text-center">
          <h2 className="text-4xl font-bold text-gray-900 mb-8">
            🚀 Начните свой путь в мире медиа
          </h2>
          <div className="flex flex-col sm:flex-row justify-center space-y-4 sm:space-y-0 sm:space-x-6">
            <Button size="lg" className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white px-8 py-4 text-lg font-semibold shadow-lg hover:shadow-xl transition-all duration-300" asChild>
              <a href="/register">
                <UserPlus className="h-5 w-5 mr-2" />
                Подать заявку
              </a>
            </Button>
            <Button variant="outline" size="lg" className="border-2 border-gray-300 hover:border-blue-500 text-gray-700 hover:text-blue-600 px-8 py-4 text-lg font-semibold shadow-lg hover:shadow-xl transition-all duration-300" asChild>
              <a href="/media-list">
                <Users className="h-5 w-5 mr-2" />
                Посмотреть медиа
              </a>
            </Button>
          </div>
          
          <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-all duration-300">
              <div className="text-blue-600 text-4xl mb-4">💰</div>
              <h3 className="text-xl font-bold mb-2">Зарабатывайте MC</h3>
              <p className="text-gray-600">Подавайте отчеты и получайте медиа-коины за активность</p>
            </div>
            
            <div className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-all duration-300">
              <div className="text-purple-600 text-4xl mb-4">🛒</div>
              <h3 className="text-xl font-bold mb-2">Тратьте в магазине</h3>
              <p className="text-gray-600">Покупайте премиум функции и эксклюзивные товары</p>
            </div>
            
            <div className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-all duration-300">
              <div className="text-green-600 text-4xl mb-4">🎯</div>
              <h3 className="text-xl font-bold mb-2">Развивайте канал</h3>
              <p className="text-gray-600">Получайте поддержку и инструменты для роста</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Registration Page
const RegisterPage = () => {
  const { toast } = useToast();
  const [formData, setFormData] = useState({
    nickname: '',
    login: '',
    password: '',
    vk_link: '',
    channel_link: ''
  });
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});

  const validateForm = () => {
    const newErrors = {};
    
    // Password validation
    if (formData.password.length < 8) {
      newErrors.password = 'Пароль должен содержать минимум 8 символов';
    }
    
    // VK link validation
    if (formData.vk_link && !formData.vk_link.includes('vk.com')) {
      newErrors.vk_link = 'Это должна быть ссылка на VK';
    }
    
    // Channel link validation  
    if (formData.channel_link && !['t.me', 'youtube.com', 'youtu.be', 'instagram.com'].some(domain => formData.channel_link.includes(domain))) {
      newErrors.channel_link = 'Ссылка должна вести на Telegram, YouTube или Instagram';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      toast({
        title: "❌ Ошибки в форме",
        description: "Пожалуйста, исправьте ошибки в форме",
        variant: "destructive",
      });
      return;
    }
    
    setLoading(true);
    try {
      await axios.post(`${API}/register`, formData);
      toast({
        title: "✅ Заявка подана!",
        description: "Заявка на регистрацию отправлена! Ожидайте одобрения администратора.",
      });
      setFormData({ nickname: '', login: '', password: '', vk_link: '', channel_link: '' });
      setErrors({});
    } catch (error) {
      toast({
        title: "❌ Ошибка регистрации",
        description: error.response?.data?.detail || error.message,
        variant: "destructive",
      });
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl">Регистрация</CardTitle>
          <CardDescription>Подайте заявку на участие в SwagMedia</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label htmlFor="nickname">Никнейм</Label>
              <Input
                id="nickname"
                value={formData.nickname}
                onChange={(e) => setFormData({...formData, nickname: e.target.value})}
                required
              />
            </div>
            
            <div>
              <Label htmlFor="login">Логин</Label>
              <Input
                id="login"
                value={formData.login}
                onChange={(e) => setFormData({...formData, login: e.target.value})}
                required
              />
            </div>
            
            <div>
              <Label htmlFor="password">Пароль (минимум 8 символов)</Label>
              <Input
                id="password"
                type="password"
                value={formData.password}
                onChange={(e) => setFormData({...formData, password: e.target.value})}
                required
                className={errors.password ? 'border-red-500' : ''}
              />
              {errors.password && <p className="text-red-500 text-sm mt-1">{errors.password}</p>}
            </div>
            
            <div>
              <Label htmlFor="vk_link">Ссылка на VK</Label>
              <Input
                id="vk_link"
                value={formData.vk_link}
                onChange={(e) => setFormData({...formData, vk_link: e.target.value})}
                placeholder="https://vk.com/username"
                required
                className={errors.vk_link ? 'border-red-500' : ''}
              />
              {errors.vk_link && <p className="text-red-500 text-sm mt-1">{errors.vk_link}</p>}
            </div>
            
            <div>
              <Label htmlFor="channel_link">Ссылка на канал</Label>
              <Input
                id="channel_link"
                value={formData.channel_link}
                onChange={(e) => setFormData({...formData, channel_link: e.target.value})}
                placeholder="https://t.me/channel или https://youtube.com/channel"
                required
                className={errors.channel_link ? 'border-red-500' : ''}
              />
              {errors.channel_link && <p className="text-red-500 text-sm mt-1">{errors.channel_link}</p>}
            </div>

            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? 'Подача заявки...' : 'Подать заявку'}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};

// Login Page
const LoginPage = () => {
  const { login } = useAuth();
  const { toast } = useToast();
  const [formData, setFormData] = useState({ login: '', password: '' });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await axios.post(`${API}/login`, formData);
      login(response.data.access_token, response.data.user);
      toast({
        title: "✅ Успешный вход!",
        description: `Добро пожаловать, ${response.data.user.nickname}!`,
      });
      // Force page reload to ensure proper navigation
      setTimeout(() => {
        window.location.href = '/';
      }, 1000);
    } catch (error) {
      toast({
        title: "❌ Ошибка входа",
        description: error.response?.data?.detail || error.message,
        variant: "destructive",
      });
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl">Авторизация</CardTitle>
          <CardDescription>Войдите в свой аккаунт</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label htmlFor="login">Логин</Label>
              <Input
                id="login"
                value={formData.login}
                onChange={(e) => setFormData({...formData, login: e.target.value})}
                required
              />
            </div>
            
            <div>
              <Label htmlFor="password">Пароль</Label>
              <Input
                id="password"
                type="password"
                value={formData.password}
                onChange={(e) => setFormData({...formData, password: e.target.value})}
                required
              />
            </div>

            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? 'Вход...' : 'Войти'}
            </Button>
          </form>

          <div className="mt-4 text-center">
            <Button variant="link" asChild>
              <a href="/register">Нет аккаунта? Подать заявку</a>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// Media List Page
const MediaListPage = () => {
  const { user, isAuthenticated } = useAuth();
  const { toast } = useToast();
  const [mediaList, setMediaList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [previews, setPreviews] = useState(null);
  const [accessingUser, setAccessingUser] = useState(null);

  useEffect(() => {
    fetchMediaList();
    if (isAuthenticated) {
      fetchPreviews();
    }
  }, [isAuthenticated]);

  const fetchMediaList = async () => {
    try {
      const response = await axios.get(`${API}/media-list`);
      setMediaList(response.data);
    } catch (error) {
      console.error('Failed to fetch media list:', error);
    }
    setLoading(false);
  };

  const fetchPreviews = async () => {
    try {
      const response = await axios.get(`${API}/user/previews`);
      setPreviews(response.data);
    } catch (error) {
      console.error('Failed to fetch previews:', error);
    }
  };

  const accessMedia = async (mediaUserId) => {
    if (!isAuthenticated) {
      toast({
        title: "❌ Требуется авторизация",
        description: "Войдите в систему для доступа к медиа",
        variant: "destructive",
      });
      return;
    }

    setAccessingUser(mediaUserId);
    try {
      const response = await axios.post(`${API}/media/${mediaUserId}/access`);
      
      if (response.data.access_type === 'preview') {
        toast({
          title: "🔍 Предварительный просмотр",
          description: response.data.message,
          variant: "default",
        });
        // Refresh previews data
        fetchPreviews();
      } else {
        toast({
          title: "✅ Полный доступ",
          description: response.data.message,
        });
      }
      
      // Show access data in modal
      setAccessData(response.data.data);
      setShowAccessModal(true);
      
    } catch (error) {
      toast({
        title: "❌ Ошибка доступа",
        description: error.response?.data?.detail || error.message,
        variant: "destructive",
      });
      
      if (error.response?.status === 403) {
        // Refresh previews to show updated state
        fetchPreviews();
      }
    } finally {
      setAccessingUser(null);
    }
  };

  const [accessData, setAccessData] = useState(null);
  const [showAccessModal, setShowAccessModal] = useState(false);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 p-4">
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold">Список медиа</h1>
          
          {/* Preview Status Card */}
          {isAuthenticated && previews && (
            <Card className="w-auto">
              <CardContent className="p-4">
                <div className="flex items-center space-x-4">
                  <div className="text-center">
                    <p className="text-sm text-gray-600">Предпросмотры</p>
                    <p className="text-lg font-bold">
                      {previews.previews_remaining}/{previews.preview_limit}
                    </p>
                  </div>
                  {previews.is_blacklisted && (
                    <Badge variant="destructive">
                      Заблокирован до {new Date(previews.blacklist_until).toLocaleDateString('ru-RU')}
                    </Badge>
                  )}
                  {user?.media_type === 1 && (
                    <Badge>
                      Платный аккаунт
                    </Badge>
                  )}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
        
        {loading ? (
          <div className="text-center">Загрузка...</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {mediaList.map((media, index) => (
              <Card key={index} className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    {media.nickname}
                    <div className="flex gap-2">
                      <Badge variant={media.media_type === 'Платное' ? 'default' : 'secondary'}>
                        {media.media_type}
                      </Badge>
                      {!media.can_access && !isAuthenticated && (
                        <Badge variant="outline">
                          Требуется вход
                        </Badge>
                      )}
                    </div>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {/* Show links only if user can access or has accessed */}
                    {(media.can_access || !isAuthenticated) && (
                      <>
                        <div>
                          <strong>Канал:</strong>{' '}
                          <a 
                            href={media.channel_link} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="text-blue-600 hover:underline"
                          >
                            Перейти
                          </a>
                        </div>
                        <div>
                          <strong>VK:</strong>{' '}
                          <a 
                            href={media.vk_link} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="text-blue-600 hover:underline"
                          >
                            Профиль
                          </a>
                        </div>
                      </>
                    )}
                    
                    {/* Access button for paid content */}
                    {!media.can_access && isAuthenticated && media.media_type === 'Платное' && (
                      <Button 
                        onClick={() => accessMedia(media.id)}
                        disabled={accessingUser === media.id || (previews?.is_blacklisted)}
                        className="w-full"
                        variant="outline"
                      >
                        {accessingUser === media.id ? 'Получение доступа...' : 
                         previews?.is_blacklisted ? 'Доступ заблокирован' :
                         `Просмотреть (${previews?.previews_remaining || 0} осталось)`}
                      </Button>
                    )}
                    
                    {!media.can_access && !isAuthenticated && (
                      <Button 
                        onClick={() => toast({
                          title: "❌ Требуется авторизация", 
                          description: "Войдите в систему для доступа к медиа",
                          variant: "destructive"
                        })}
                        className="w-full"
                        variant="outline"
                      >
                        Войти для доступа
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* Access Modal */}
        <Dialog open={showAccessModal} onOpenChange={setShowAccessModal}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Доступ к медиа</DialogTitle>
              <DialogDescription>
                Информация о доступе к выбранному медиа
              </DialogDescription>
            </DialogHeader>
            {accessData && (
              <div className="space-y-3">
                <div>
                  <strong>Никнейм:</strong> {accessData.nickname}
                </div>
                <div>
                  <strong>Канал:</strong>{' '}
                  <a 
                    href={accessData.channel_link.includes('...') ? '#' : accessData.channel_link}
                    target="_blank" 
                    rel="noopener noreferrer"
                    className={accessData.channel_link.includes('...') ? 'text-gray-500' : 'text-blue-600 hover:underline'}
                  >
                    {accessData.channel_link}
                  </a>
                </div>
                <div>
                  <strong>VK:</strong>{' '}
                  <a 
                    href={accessData.vk_link.includes('...') ? '#' : accessData.vk_link}
                    target="_blank" 
                    rel="noopener noreferrer"
                    className={accessData.vk_link.includes('...') ? 'text-gray-500' : 'text-blue-600 hover:underline'}
                  >
                    {accessData.vk_link}
                  </a>
                </div>
                {accessData.preview_note && (
                  <Alert>
                    <AlertDescription>
                      {accessData.preview_note}
                    </AlertDescription>
                  </Alert>
                )}
              </div>
            )}
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
};

// Profile Page
const ProfilePage = () => {
  const { user, isAuthenticated, isLoading } = useAuth();
  const [reports, setReports] = useState([]);

  useEffect(() => {
    if (isAuthenticated && !isLoading) {
      fetchReports();
    }
  }, [isAuthenticated, isLoading]);

  const fetchReports = async () => {
    try {
      const response = await axios.get(`${API}/reports/my`);
      setReports(response.data);
    } catch (error) {
      console.error('Failed to fetch reports:', error);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 flex items-center justify-center">
        <div className="text-xl">Загрузка...</div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 p-4">
      <div className="max-w-4xl mx-auto">
        <Card className="mb-6 bg-gradient-to-br from-blue-50 to-purple-50 border-0 shadow-xl">
          <CardHeader className="pb-4">
            <div className="flex items-center justify-between">
              <CardTitle className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                👤 {user.nickname}
              </CardTitle>
              <div className="flex space-x-2">
                <Badge variant={user.media_type === 1 ? 'default' : 'secondary'} className="text-sm">
                  {user.media_type === 1 ? '💎 Платное медиа' : '🆓 Бесплатное медиа'}
                </Badge>
                {user.admin_level > 0 && (
                  <Badge variant="destructive" className="text-sm">
                    🛡️ Администратор
                  </Badge>
                )}
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div className="space-y-4">
                <h3 className="font-semibold text-lg text-gray-800 mb-4">📊 Основная информация</h3>
                <div className="space-y-3">
                  <div className="bg-white rounded-lg p-3 shadow-sm">
                    <div className="flex items-center space-x-2">
                      <span className="text-2xl">📺</span>
                      <div>
                        <strong>Канал:</strong> 
                        <a href={user.channel_link} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline ml-2">
                          Перейти →
                        </a>
                      </div>
                    </div>
                  </div>
                  <div className="bg-white rounded-lg p-3 shadow-sm">
                    <div className="flex items-center space-x-2">
                      <span className="text-2xl">👥</span>
                      <div>
                        <strong>VK профиль:</strong> 
                        <a href={user.vk_link} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline ml-2">
                          Открыть →
                        </a>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="space-y-4">
                <h3 className="font-semibold text-lg text-gray-800 mb-4">📈 Ваша статистика</h3>
                <div className="space-y-3">
                  <div className="bg-white rounded-lg p-4 shadow-sm">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <Coins className="h-8 w-8 text-yellow-600" />
                        <div>
                          <div className="text-sm text-gray-500">Медиа-коины</div>
                          <div className="text-2xl font-bold text-gray-900">{user.balance?.toLocaleString() || 0} MC</div>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <div className="bg-white rounded-lg p-4 shadow-sm">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <AlertTriangle className={`h-8 w-8 ${user.warnings >= 2 ? 'text-red-600' : 'text-gray-400'}`} />
                        <div>
                          <div className="text-sm text-gray-500">Предупреждения</div>
                          <div className={`text-2xl font-bold ${user.warnings >= 2 ? 'text-red-600' : 'text-gray-900'}`}>
                            {user.warnings || 0}/3
                          </div>
                        </div>
                      </div>
                      {user.warnings >= 2 && (
                        <Badge variant="destructive">Опасная зона!</Badge>
                      )}
                    </div>
                  </div>
                  
                  <div className="bg-white rounded-lg p-4 shadow-sm">
                    <div className="flex items-center space-x-3">
                      <FileText className="h-8 w-8 text-blue-600" />
                      <div>
                        <div className="text-sm text-gray-500">Отчетов подано</div>
                        <div className="text-2xl font-bold text-gray-900">{reports.length}</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="shadow-xl">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <FileText className="h-6 w-6 text-blue-600" />
              <span>📝 История ваших отчетов</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {reports.length === 0 ? (
              <div className="text-center py-8">
                <div className="text-6xl mb-4">📄</div>
                <div className="text-gray-500 text-lg">Отчетов пока нет</div>
                <Button className="mt-4" asChild>
                  <a href="/reports">Подать первый отчет</a>
                </Button>
              </div>
            ) : (
              <div className="space-y-4">
                {reports.map((report) => (
                  <div key={report.id} className={`border rounded-lg p-4 ${
                    report.status === 'approved' ? 'bg-green-50 border-green-200' :
                    report.status === 'rejected' ? 'bg-red-50 border-red-200' : 'bg-yellow-50 border-yellow-200'
                  }`}>
                    <div className="flex justify-between items-start mb-3">
                      <div className="text-sm text-gray-600">
                        📅 {new Date(report.created_at).toLocaleString('ru-RU')}
                      </div>
                      <Badge variant={
                        report.status === 'approved' ? 'default' :
                        report.status === 'rejected' ? 'destructive' : 'secondary'
                      }>
                        {report.status === 'approved' ? '✅ Одобрен' :
                         report.status === 'rejected' ? '❌ Отклонен' : '⏳ На рассмотрении'}
                      </Badge>
                    </div>
                    <div className="space-y-2">
                      {report.links.map((link, index) => (
                        <div key={index} className="flex justify-between items-center bg-white rounded p-2">
                          <a href={link.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline flex-1 truncate">
                            🔗 {link.url}
                          </a>
                          <span className="text-sm font-semibold text-gray-600 ml-4">
                            👁️ {link.views.toLocaleString()} просмотров
                          </span>
                        </div>
                      ))}
                    </div>
                    {report.admin_comment && (
                      <div className="mt-3 p-3 bg-blue-50 rounded-lg">
                        <div className="text-sm font-semibold text-blue-800 mb-1">💬 Комментарий администратора:</div>
                        <div className="text-sm text-blue-700">{report.admin_comment}</div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

// Shop Page
const ShopPage = () => {
  const { isAuthenticated, user, isLoading } = useAuth();
  const { toast } = useToast();
  const [items, setItems] = useState([]);
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchShopItems();
  }, []);

  const fetchShopItems = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/shop/items`);
      console.log('Shop items response:', response.data);
      const itemsData = response.data || [];
      setItems(itemsData);
      
      if (itemsData.length > 0) {
        const uniqueCategories = [...new Set(itemsData.map(item => item.category))];
        console.log('Categories found:', uniqueCategories);
        setCategories(uniqueCategories);
        toast({
          title: "🛍️ Магазин загружен",
          description: `Найдено ${itemsData.length} товаров в ${uniqueCategories.length} категориях`,
        });
      } else {
        toast({
          title: "⚠️ Товары не найдены",
          description: "Пожалуйста, обратитесь к администратору.",
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error('Failed to fetch shop items:', error);
      toast({
        title: "❌ Ошибка загрузки",
        description: "Не удалось загрузить товары. Попробуйте обновить страницу.",
        variant: "destructive",
      });
    }
    setLoading(false);
  };

  const handlePurchase = async (itemId) => {
    if (!isAuthenticated) {
      toast({
        title: "🔒 Требуется авторизация",
        description: "Войдите в аккаунт для совершения покупок",
        variant: "destructive",
      });
      return;
    }

    try {
      await axios.post(`${API}/shop/purchase`, { item_id: itemId });
      toast({
        title: "✅ Заявка подана!",
        description: "Ваша заявка на покупку отправлена администратору на рассмотрение.",
      });
    } catch (error) {
      toast({
        title: "❌ Ошибка покупки",
        description: error.response?.data?.detail || error.message,
        variant: "destructive",
      });
    }
  };

  const filteredItems = selectedCategory === 'all' 
    ? items 
    : items.filter(item => item.category === selectedCategory);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 flex items-center justify-center">
        <div className="text-xl">Загрузка...</div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 p-4">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold mb-4 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Магазин SwagMedia
          </h1>
          <div className="flex items-center justify-center space-x-3 mb-4">
            <div className="bg-white rounded-lg shadow-lg px-6 py-3 flex items-center space-x-3">
              <Coins className="h-8 w-8 text-yellow-600" />
              <div>
                <div className="text-sm text-gray-500">Ваш баланс</div>
                <div className="text-2xl font-bold text-gray-900">{user?.balance?.toLocaleString() || 0} MC</div>
              </div>
            </div>
          </div>
          <p className="text-gray-600 max-w-2xl mx-auto">
            Приобретайте эксклюзивные товары и услуги за медиа-коины. Зарабатывайте MC подавая отчеты!
          </p>
        </div>

        {categories.length > 0 && (
          <div className="mb-8">
            <div className="flex flex-wrap justify-center gap-3 mb-4">
              <Button
                variant={selectedCategory === 'all' ? 'default' : 'outline'}
                onClick={() => setSelectedCategory('all')}
                className="transition-all duration-200"
              >
                Все категории ({items.length})
              </Button>
              {categories.map(category => {
                const categoryCount = items.filter(item => item.category === category).length;
                return (
                  <Button
                    key={category}
                    variant={selectedCategory === category ? 'default' : 'outline'}
                    onClick={() => setSelectedCategory(category)}
                    className="transition-all duration-200"
                  >
                    {category} ({categoryCount})
                  </Button>
                );
              })}
            </div>
          </div>
        )}

        {loading ? (
          <div className="text-center">Загрузка товаров...</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredItems.map((item) => (
              <Card key={item.id} className="hover:shadow-lg transition-all duration-300 hover:scale-105">
                <CardHeader className="pb-3">
                  {/* Image display */}
                  {item.image_url ? (
                    <div className="w-full h-32 mb-3 rounded-lg overflow-hidden bg-gray-100">
                      <img 
                        src={item.image_url} 
                        alt={item.name}
                        className="w-full h-full object-cover"
                        onError={(e) => {
                          e.target.style.display = 'none';
                          e.target.nextSibling.style.display = 'flex';
                        }}
                      />
                      <div className="hidden w-full h-full items-center justify-center bg-gray-100 text-gray-500">
                        <Image className="h-8 w-8" />
                      </div>
                    </div>
                  ) : (
                    <div className="w-full h-32 mb-3 rounded-lg bg-gray-100 flex items-center justify-center">
                      <div className="text-center">
                        <Image className="h-8 w-8 mx-auto text-gray-400 mb-1" />
                        <span className="text-xs text-gray-500">
                          {item.category === 'Премиум' ? '🏆' : item.category === 'Буст' ? '🚀' : '🎨'}
                        </span>
                      </div>
                    </div>
                  )}
                  
                  <div className="flex items-start justify-between">
                    <CardTitle className="text-lg font-semibold text-gray-800 leading-tight">
                      {item.name}
                    </CardTitle>
                    <Badge 
                      variant={item.category === 'Премиум' ? 'default' : 
                              item.category === 'Буст' ? 'secondary' : 'outline'}
                      className="ml-2 flex-shrink-0"
                    >
                      {item.category}
                    </Badge>
                  </div>
                  <CardDescription className="text-sm text-gray-600 mt-2">
                    {item.description}
                  </CardDescription>
                </CardHeader>
                <CardContent className="pt-0">
                  <div className="flex justify-between items-center">
                    <div className="flex items-center space-x-2">
                      <Coins className="h-5 w-5 text-yellow-600" />
                      <span className="text-xl font-bold text-gray-900">{item.price} MC</span>
                    </div>
                    <Button 
                      onClick={() => handlePurchase(item.id)}
                      disabled={user?.balance < item.price}
                      className={user?.balance < item.price ? 
                        "bg-gray-400 cursor-not-allowed" : 
                        "bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"}
                    >
                      {user?.balance < item.price ? 'Недостаточно MC' : 'Купить'}
                    </Button>
                  </div>
                  
                  {/* Progress bar showing affordability */}
                  {user && (
                    <div className="mt-3">
                      <div className="flex justify-between text-xs text-gray-500 mb-1">
                        <span>Ваш баланс: {user.balance} MC</span>
                        <span>{user.balance >= item.price ? '✅ Доступно' : '❌ Нужно больше MC'}</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div 
                          className={`h-2 rounded-full transition-all duration-300 ${
                            user.balance >= item.price 
                              ? 'bg-gradient-to-r from-green-400 to-green-600' 
                              : 'bg-gradient-to-r from-red-400 to-orange-500'
                          }`}
                          style={{ width: `${Math.min(100, (user.balance / item.price) * 100)}%` }}
                        ></div>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {!loading && filteredItems.length === 0 && items.length > 0 && (
          <div className="text-center text-gray-500">
            Нет товаров в категории "{selectedCategory}"
          </div>
        )}
        
        {!loading && items.length === 0 && (
          <div className="text-center text-gray-500">
            Товары загружаются... Если товары не появились, обновите страницу.
          </div>
        )}
        
        {!loading && filteredItems.length > 0 && (
          <div className="mb-4 text-center">
            <p className="text-gray-600">Найдено товаров: {filteredItems.length} из {items.length}</p>
          </div>
        )}
      </div>
    </div>
  );
};

// Reports Page
const ReportsPage = () => {
  const { isAuthenticated, isLoading } = useAuth();
  const { toast } = useToast();
  const [links, setLinks] = useState([{ url: '', views: 0 }]);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const validLinks = links.filter(link => link.url);
      if (validLinks.length === 0) {
        toast({
          title: "⚠️ Нет ссылок",
          description: "Добавьте хотя бы одну ссылку для отчета",
          variant: "destructive",
        });
        setLoading(false);
        return;
      }

      await axios.post(`${API}/reports`, { links: validLinks });
      toast({
        title: "✅ Отчет подан!",
        description: "Ваш отчет успешно отправлен на рассмотрение администратору.",
      });
      setLinks([{ url: '', views: 0 }]);
    } catch (error) {
      toast({
        title: "❌ Ошибка отправки",
        description: error.response?.data?.detail || error.message,
        variant: "destructive",
      });
    }
    setLoading(false);
  };

  const addLink = () => {
    setLinks([...links, { url: '', views: 0 }]);
  };

  const removeLink = (index) => {
    setLinks(links.filter((_, i) => i !== index));
  };

  const updateLink = (index, field, value) => {
    const newLinks = [...links];
    newLinks[index][field] = field === 'views' ? parseInt(value) || 0 : value;
    setLinks(newLinks);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 flex items-center justify-center">
        <div className="text-xl">Загрузка...</div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 p-4">
      <div className="max-w-2xl mx-auto">
        <Card>
          <CardHeader>
            <CardTitle>Подача отчета</CardTitle>
            <CardDescription>Добавьте ссылки на ваши видео и укажите количество просмотров</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit}>
              <div className="space-y-4">
                {links.map((link, index) => (
                  <div key={index} className="flex space-x-2 items-end">
                    <div className="flex-1">
                      <Label htmlFor={`url-${index}`}>Ссылка на видео</Label>
                      <Input
                        id={`url-${index}`}
                        value={link.url}
                        onChange={(e) => updateLink(index, 'url', e.target.value)}
                        placeholder="https://..."
                        required
                      />
                    </div>
                    <div className="w-32">
                      <Label htmlFor={`views-${index}`}>Просмотры</Label>
                      <Input
                        id={`views-${index}`}
                        type="number"
                        value={link.views}
                        onChange={(e) => updateLink(index, 'views', e.target.value)}
                        required
                      />
                    </div>
                    {links.length > 1 && (
                      <Button 
                        type="button" 
                        variant="outline" 
                        size="sm"
                        onClick={() => removeLink(index)}
                      >
                        ✕
                      </Button>
                    )}
                  </div>
                ))}
                
                <Button type="button" variant="outline" onClick={addLink}>
                  + Добавить ссылку
                </Button>
              </div>

              <div className="mt-6">
                <Button type="submit" disabled={loading} className="w-full">
                  {loading ? 'Отправка...' : 'Подать отчет'}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

// Admin Page
const AdminPage = () => {
  const { user, isAuthenticated, isLoading } = useAuth();
  const { toast } = useToast();
  const [applications, setApplications] = useState([]);
  const [purchases, setPurchases] = useState([]);
  const [reports, setReports] = useState([]);
  const [users, setUsers] = useState([]);
  const [stats, setStats] = useState(null);
  const [advancedStats, setAdvancedStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('stats'); // Start with stats tab
  
  // Search and Filter States
  const [userSearch, setUserSearch] = useState('');
  const [reportFilter, setReportFilter] = useState('all'); // all, pending, approved, rejected
  const [applicationFilter, setApplicationFilter] = useState('all'); // all, pending, approved, rejected
  const [purchaseFilter, setPurchaseFilter] = useState('all'); // all, pending, approved, rejected
  const [sortBy, setSortBy] = useState('date'); // date, name, balance
  const [sortOrder, setSortOrder] = useState('desc'); // asc, desc
  
  // Pagination States
  const [currentPage, setCurrentPage] = useState({
    applications: 1,
    purchases: 1,
    reports: 1,
    users: 1
  });
  const [itemsPerPage] = useState(10);

  // Modal states для предупреждений
  const [showWarningModal, setShowWarningModal] = useState(false);
  const [warningUser, setWarningUser] = useState(null);
  const [warningReason, setWarningReason] = useState('');

  // Modal states для переключения типа медиа  
  const [showMediaTypeModal, setShowMediaTypeModal] = useState(false);
  const [mediaTypeUser, setMediaTypeUser] = useState(null);
  const [mediaTypeComment, setMediaTypeComment] = useState('');

  useEffect(() => {
    if (isAuthenticated && !isLoading && user?.admin_level >= 1) {
      fetchAdminData();
    }
  }, [isAuthenticated, isLoading, user]);

  const fetchAdminData = async () => {
    setLoading(true);
    try {
      const [appsRes, purchasesRes, reportsRes, usersRes, statsRes, advancedStatsRes] = await Promise.all([
        axios.get(`${API}/admin/applications`),
        axios.get(`${API}/admin/purchases`),
        axios.get(`${API}/admin/reports`),
        axios.get(`${API}/admin/users`),
        axios.get(`${API}/stats`),
        axios.get(`${API}/stats/advanced`)
      ]);
      
      setApplications(appsRes.data || []);
      setPurchases(purchasesRes.data || []);
      setReports(reportsRes.data || []);
      setUsers(usersRes.data || []);
      setStats(statsRes.data || {});
      setAdvancedStats(advancedStatsRes.data || {});
      
      const pendingCount = (appsRes.data || []).filter(app => app.status === 'pending').length;
      if (pendingCount > 0) {
        toast({
          title: "📋 Новые заявки",
          description: `У вас ${pendingCount} новых заявок на рассмотрении`,
        });
      }
    } catch (error) {
      console.error('Failed to fetch admin data:', error);
      toast({
        title: "❌ Ошибка загрузки",
        description: "Не удалось загрузить данные админ панели",
        variant: "destructive",
      });
    }
    setLoading(false);
  };

  const handleApplicationAction = async (appId, action, mediaType = 0) => {
    try {
      const app = applications.find(a => a.id === appId);
      if (action === 'approve') {
        await axios.post(`${API}/admin/applications/${appId}/approve?media_type=${mediaType}`);
        toast({
          title: "✅ Заявка одобрена!",
          description: `Пользователь ${app?.data?.nickname} добавлен в систему как ${mediaType === 1 ? 'платное' : 'бесплатное'} медиа`,
        });
      } else {
        await axios.post(`${API}/admin/applications/${appId}/reject`);
        toast({
          title: "❌ Заявка отклонена",
          description: `Заявка от ${app?.data?.nickname} была отклонена`,
          variant: "destructive",
        });
      }
      fetchAdminData();
    } catch (error) {
      console.error('Action failed:', error);
      toast({
        title: "❌ Ошибка операции",
        description: "Не удалось выполнить действие",
        variant: "destructive",
      });
    }
  };

  const handlePurchaseAction = async (purchaseId, action) => {
    try {
      const purchase = purchases.find(p => p.id === purchaseId);
      if (action === 'approve') {
        await axios.post(`${API}/admin/purchases/${purchaseId}/approve`);
        toast({
          title: "✅ Покупка одобрена!",
          description: `Покупка товара "${purchase?.item_name}" пользователем ${purchase?.user_nickname} одобрена`,
        });
      } else {
        await axios.post(`${API}/admin/purchases/${purchaseId}/reject`);
        toast({
          title: "❌ Покупка отклонена",
          description: `Покупка товара "${purchase?.item_name}" была отклонена`,
          variant: "destructive",
        });
      }
      fetchAdminData();
    } catch (error) {
      console.error('Action failed:', error);
      toast({
        title: "❌ Ошибка операции",
        description: "Не удалось выполнить действие",
        variant: "destructive",
      });
    }
  };

  const handleReportApprove = async (reportId, customMc = null, comment = '') => {
    try {
      const report = reports.find(r => r.id === reportId);
      const requestData = {
        comment: comment,
        mc_reward: customMc
      };
      
      await axios.post(`${API}/admin/reports/${reportId}/approve`, requestData);
      toast({
        title: "✅ Отчет одобрен!",
        description: `Отчет от ${report?.user_nickname} одобрен. ${customMc || 'Автоматически рассчитанные'} MC начислены на баланс.`,
      });
      fetchAdminData();
    } catch (error) {
      console.error('Action failed:', error);
      toast({
        title: "❌ Ошибка операции",
        description: "Не удалось выполнить действие",
        variant: "destructive",
      });
    }
  };

  const downloadExport = async (dataType) => {
    try {
      const response = await axios.get(`${API}/admin/export/${dataType}`, {
        responseType: 'blob',
      });
      
      // Create blob link to download
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      
      // Get filename from response headers or use default
      const contentDisposition = response.headers['content-disposition'];
      let filename = `${dataType}.csv`;
      if (contentDisposition) {
        const filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
        const matches = filenameRegex.exec(contentDisposition);
        if (matches != null && matches[1]) { 
          filename = matches[1].replace(/['"]/g, '');
        }
      }
      
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      toast({
        title: "📁 Экспорт завершен",
        description: `Данные "${dataType}" успешно скачаны`,
      });
    } catch (error) {
      console.error('Export failed:', error);
      toast({
        title: "❌ Ошибка экспорта",
        description: "Не удалось скачать данные",
        variant: "destructive",
      });
    }
  };

  // Filter and Sort Functions
  const filterApplications = (apps) => {
    let filtered = [...apps];
    
    if (applicationFilter !== 'all') {
      filtered = filtered.filter(app => app.status === applicationFilter);
    }
    
    // Sort
    filtered.sort((a, b) => {
      let comparison = 0;
      if (sortBy === 'date') {
        comparison = new Date(a.created_at) - new Date(b.created_at);
      } else if (sortBy === 'name') {
        comparison = (a.data?.nickname || '').localeCompare(b.data?.nickname || '');
      }
      return sortOrder === 'desc' ? -comparison : comparison;
    });
    
    return filtered;
  };

  const filterPurchases = (purchases) => {
    let filtered = [...purchases];
    
    if (purchaseFilter !== 'all') {
      filtered = filtered.filter(purchase => purchase.status === purchaseFilter);
    }
    
    // Sort
    filtered.sort((a, b) => {
      let comparison = 0;
      if (sortBy === 'date') {
        comparison = new Date(a.created_at) - new Date(b.created_at);
      } else if (sortBy === 'name') {
        comparison = (a.user_nickname || '').localeCompare(b.user_nickname || '');
      }
      return sortOrder === 'desc' ? -comparison : comparison;
    });
    
    return filtered;
  };

  const filterReports = (reports) => {
    let filtered = [...reports];
    
    if (reportFilter !== 'all') {
      filtered = filtered.filter(report => report.status === reportFilter);
    }
    
    // Sort
    filtered.sort((a, b) => {
      let comparison = 0;
      if (sortBy === 'date') {
        comparison = new Date(a.created_at) - new Date(b.created_at);
      } else if (sortBy === 'name') {
        comparison = (a.user_nickname || '').localeCompare(b.user_nickname || '');
      }
      return sortOrder === 'desc' ? -comparison : comparison;
    });
    
    return filtered;
  };

  const filterUsers = (users) => {
    let filtered = [...users];
    
    // Search filter
    if (userSearch) {
      filtered = filtered.filter(user => 
        user.nickname?.toLowerCase().includes(userSearch.toLowerCase()) ||
        user.login?.toLowerCase().includes(userSearch.toLowerCase())
      );
    }
    
    // Sort
    filtered.sort((a, b) => {
      let comparison = 0;
      if (sortBy === 'date') {
        comparison = new Date(a.created_at || 0) - new Date(b.created_at || 0);
      } else if (sortBy === 'name') {
        comparison = (a.nickname || '').localeCompare(b.nickname || '');
      } else if (sortBy === 'balance') {
        comparison = (a.balance || 0) - (b.balance || 0);
      }
      return sortOrder === 'desc' ? -comparison : comparison;
    });
    
    return filtered;
  };

  // Pagination Functions
  const paginateData = (data, page, perPage = itemsPerPage) => {
    const startIndex = (page - 1) * perPage;
    const endIndex = startIndex + perPage;
    return {
      data: data.slice(startIndex, endIndex),
      totalPages: Math.ceil(data.length / perPage),
      totalItems: data.length
    };
  };

  const changePage = (tab, page) => {
    setCurrentPage(prev => ({ ...prev, [tab]: page }));
  };

  // Pagination Component
  const PaginationControls = ({ currentPageNum, totalPages, onPageChange, totalItems }) => {
    if (totalPages <= 1) return null;
    
    return (
      <div className="flex items-center justify-between mt-6 px-4">
        <div className="text-sm text-gray-600">
          Показано {Math.min(itemsPerPage * (currentPageNum - 1) + 1, totalItems)} - {Math.min(itemsPerPage * currentPageNum, totalItems)} из {totalItems}
        </div>
        <div className="flex space-x-2">
          <Button
            variant="outline"
            size="sm"
            disabled={currentPageNum === 1}
            onClick={() => onPageChange(currentPageNum - 1)}
          >
            Предыдущая
          </Button>
          
          {[...Array(totalPages)].map((_, i) => {
            const pageNum = i + 1;
            if (
              pageNum === 1 ||
              pageNum === totalPages ||
              (pageNum >= currentPageNum - 2 && pageNum <= currentPageNum + 2)
            ) {
              return (
                <Button
                  key={pageNum}
                  variant={pageNum === currentPageNum ? "default" : "outline"}
                  size="sm"
                  onClick={() => onPageChange(pageNum)}
                >
                  {pageNum}
                </Button>
              );
            } else if (
              pageNum === currentPageNum - 3 ||
              pageNum === currentPageNum + 3
            ) {
              return <span key={pageNum} className="px-2">...</span>;
            }
            return null;
          })}
          
          <Button
            variant="outline"
            size="sm"
            disabled={currentPageNum === totalPages}
            onClick={() => onPageChange(currentPageNum + 1)}
          >
            Следующая
          </Button>
        </div>
      </div>
    );
  };

  // Функция открытия модального окна предупреждения
  const openWarningModal = (user) => {
    setWarningUser(user);
    setWarningReason('');
    setShowWarningModal(true);
  };

  // Функция отправки предупреждения с причиной
  const submitWarning = async () => {
    if (!warningReason.trim()) {
      toast({
        title: "❌ Ошибка",
        description: "Укажите причину предупреждения",
        variant: "destructive",
      });
      return;
    }

    try {
      const requestData = {
        reason: warningReason.trim()
      };
      
      const response = await axios.post(`${API}/admin/users/${warningUser.id}/warning`, requestData);
      const newWarnings = (warningUser?.warnings || 0) + 1;
      
      if (newWarnings >= 3) {
        toast({
          title: "🚨 Пользователь заблокирован!",
          description: `${warningUser?.nickname} получил 3-е предупреждение и был автоматически заблокирован`,
          variant: "destructive",
        });
      } else {
        toast({
          title: "⚠️ Предупреждение выдано",
          description: `${warningUser?.nickname} получил предупреждение (${newWarnings}/3). Причина: ${warningReason}`,
        });
      }
      
      setShowWarningModal(false);
      setWarningUser(null);
      setWarningReason('');
      fetchAdminData();
    } catch (error) {
      console.error('Warning failed:', error);
      toast({
        title: "❌ Ошибка предупреждения",
        description: "Не удалось выдать предупреждение",
        variant: "destructive",
      });
    }
  };

  // Функция открытия модального окна смены типа медиа
  const openMediaTypeModal = (user) => {
    setMediaTypeUser(user);
    setMediaTypeComment('');
    setShowMediaTypeModal(true);
  };

  // Функция смены типа медиа
  const submitMediaTypeChange = async () => {
    try {
      const newMediaType = mediaTypeUser.media_type === 1 ? 0 : 1;
      const requestData = {
        user_id: mediaTypeUser.id,
        new_media_type: newMediaType,
        admin_comment: mediaTypeComment.trim()
      };
      
      await axios.post(`${API}/admin/users/${mediaTypeUser.id}/change-media-type`, requestData);
      const typeNames = {0: "Бесплатное", 1: "Платное"};
      toast({
        title: "🔄 Тип медиа изменен",
        description: `${mediaTypeUser?.nickname} теперь ${typeNames[newMediaType]} медиа. Пользователь уведомлен.`,
      });
      
      setShowMediaTypeModal(false);
      setMediaTypeUser(null);
      setMediaTypeComment('');
      fetchAdminData();
    } catch (error) {
      console.error('Media type change failed:', error);
      toast({
        title: "❌ Ошибка смены типа",
        description: "Не удалось изменить тип медиа",
        variant: "destructive",
      });
    }
  };

  const handleUserAction = async (userId, action, amount = 0) => {
    try {
      const userItem = users.find(u => u.id === userId);
      if (action === 'balance') {
        await axios.post(`${API}/admin/users/${userId}/balance?amount=${amount}`);
        toast({
          title: amount > 0 ? "💰 MC добавлены" : "💸 MC списаны",
          description: `${amount > 0 ? 'Добавлено' : 'Списано'} ${Math.abs(amount)} MC пользователю ${userItem?.nickname}`,
        });
        fetchAdminData();
      }
    } catch (error) {
      console.error('Action failed:', error);
      toast({
        title: "❌ Ошибка операции",
        description: "Не удалось выполнить действие",
        variant: "destructive",
      });
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 flex items-center justify-center">
        <div className="text-xl">Загрузка...</div>
      </div>
    );
  }

  if (!isAuthenticated || user?.admin_level < 1) {
    return <Navigate to="/" />;
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 flex items-center justify-center">
        <div className="text-xl">Загрузка админ панели...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 p-4">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold mb-4 bg-gradient-to-r from-red-600 to-purple-600 bg-clip-text text-transparent">
            🛡️ Админ панель SwagMedia
          </h1>
          <p className="text-gray-600">Управление пользователями, заявками и контентом</p>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-7">
            <TabsTrigger value="stats">📊 Статистика</TabsTrigger>
            <TabsTrigger value="applications">Заявки ({applications.filter(app => app.status === 'pending').length})</TabsTrigger>
            <TabsTrigger value="purchases">Покупки ({purchases.filter(p => p.status === 'pending').length})</TabsTrigger>
            <TabsTrigger value="reports">Отчеты ({reports.filter(r => r.status === 'pending').length})</TabsTrigger>
            <TabsTrigger value="users">Пользователи ({users.length})</TabsTrigger>
            <TabsTrigger value="shop">Магазин</TabsTrigger>
            <TabsTrigger value="blacklist">🚫 Черный список</TabsTrigger>
          </TabsList>

          {/* Statistics Dashboard Tab */}
          <TabsContent value="stats" className="mt-6">
            <div className="space-y-6">
              {/* Key Metrics Cards */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <Card>
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-gray-600">Всего пользователей</p>
                        <p className="text-2xl font-bold text-blue-600">{stats?.total_media || 0}</p>
                      </div>
                      <Users className="h-8 w-8 text-blue-500" />
                    </div>
                  </CardContent>
                </Card>
                
                <Card>
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-gray-600">Потрачено MC</p>
                        <p className="text-2xl font-bold text-green-600">{stats?.total_mc_spent?.toLocaleString() || 0}</p>
                      </div>
                      <Coins className="h-8 w-8 text-green-500" />
                    </div>
                  </CardContent>
                </Card>
                
                <Card>
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-gray-600">Текущие балансы</p>
                        <p className="text-2xl font-bold text-purple-600">{stats?.total_mc_current?.toLocaleString() || 0}</p>
                      </div>
                      <Activity className="h-8 w-8 text-purple-500" />
                    </div>
                  </CardContent>
                </Card>
                
                <Card>
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-gray-600">Всего отчетов</p>
                        <p className="text-2xl font-bold text-orange-600">{advancedStats?.report_stats?.total || 0}</p>
                      </div>
                      <FileText className="h-8 w-8 text-orange-500" />
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Charts Grid */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* User Types Pie Chart */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Users className="h-5 w-5" />
                      Типы пользователей
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="h-64">
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie
                            data={[
                              { name: 'Платные', value: advancedStats?.user_stats?.paid_users || 0, fill: '#3b82f6' },
                              { name: 'Бесплатные', value: advancedStats?.user_stats?.free_users || 0, fill: '#10b981' }
                            ]}
                            cx="50%"
                            cy="50%"
                            labelLine={false}
                            label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                            outerRadius={80}
                            fill="#8884d8"
                            dataKey="value"
                          />
                          <Tooltip />
                        </PieChart>
                      </ResponsiveContainer>
                    </div>
                  </CardContent>
                </Card>

                {/* Reports Status Bar Chart */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <FileText className="h-5 w-5" />
                      Статистика отчетов
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="h-64">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart
                          data={[
                            { name: 'Всего', count: advancedStats?.report_stats?.total || 0, fill: '#3b82f6' },
                            { name: 'Ожидают', count: advancedStats?.report_stats?.pending || 0, fill: '#f59e0b' },
                            { name: 'Одобрено', count: advancedStats?.report_stats?.approved || 0, fill: '#10b981' },
                            { name: 'Отклонено', count: advancedStats?.report_stats?.rejected || 0, fill: '#ef4444' }
                          ]}
                        >
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="name" />
                          <YAxis />
                          <Tooltip />
                          <Bar dataKey="count" />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </CardContent>
                </Card>

                {/* Monthly Reports Trend */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <TrendingUp className="h-5 w-5" />
                      Тренд отчетов по месяцам
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="h-64">
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={advancedStats?.monthly_reports || []}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="month" />
                          <YAxis />
                          <Tooltip />
                          <Line type="monotone" dataKey="count" stroke="#3b82f6" strokeWidth={3} />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  </CardContent>
                </Card>

                {/* Shop Categories */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <ShoppingCart className="h-5 w-5" />
                      Категории товаров
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="h-64">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={advancedStats?.shop_categories || []}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="category" />
                          <YAxis />
                          <Tooltip />
                          <Bar dataKey="count" fill="#8b5cf6" />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Export Buttons */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Download className="h-5 w-5" />
                    Экспорт данных
                  </CardTitle>
                  <CardDescription>
                    Скачивайте данные в формате CSV для анализа
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                    <Button
                      variant="outline"
                      onClick={() => downloadExport('users')}
                      className="w-full"
                    >
                      <Download className="h-4 w-4 mr-2" />
                      Пользователи
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => downloadExport('reports')}
                      className="w-full"
                    >
                      <Download className="h-4 w-4 mr-2" />
                      Отчеты
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => downloadExport('purchases')}
                      className="w-full"
                    >
                      <Download className="h-4 w-4 mr-2" />
                      Покупки
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => downloadExport('ratings')}
                      className="w-full"
                    >
                      <Download className="h-4 w-4 mr-2" />
                      Рейтинги
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="applications" className="mt-6">
            <Card>
              <CardHeader>
                <div className="flex flex-col sm:flex-row sm:items-center justify-between space-y-4 sm:space-y-0">
                  <CardTitle>Заявки на регистрацию</CardTitle>
                  <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-2">
                    {/* Filter by Status */}
                    <Select value={applicationFilter} onValueChange={setApplicationFilter}>
                      <SelectTrigger className="w-full sm:w-40">
                        <Filter className="h-4 w-4 mr-2" />
                        <SelectValue placeholder="Статус" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">Все статусы</SelectItem>
                        <SelectItem value="pending">Ожидание</SelectItem>
                        <SelectItem value="approved">Одобрено</SelectItem>
                        <SelectItem value="rejected">Отклонено</SelectItem>
                      </SelectContent>
                    </Select>
                    
                    {/* Sort */}
                    <div className="flex space-x-1">
                      <Select value={sortBy} onValueChange={setSortBy}>
                        <SelectTrigger className="w-full sm:w-32">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="date">Дата</SelectItem>
                          <SelectItem value="name">Имя</SelectItem>
                        </SelectContent>
                      </Select>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setSortOrder(sortOrder === 'desc' ? 'asc' : 'desc')}
                      >
                        {sortOrder === 'desc' ? <SortDesc className="h-4 w-4" /> : <SortAsc className="h-4 w-4" />}
                      </Button>
                    </div>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {(() => {
                  const filteredApps = filterApplications(applications);
                  const paginatedApps = paginateData(filteredApps, currentPage.applications);
                  
                  if (paginatedApps.totalItems === 0) {
                    return <div className="text-center text-gray-500 py-8">Нет заявок для отображения</div>;
                  }
                  
                  return (
                    <>
                      <div className="space-y-4">
                        {paginatedApps.data.map((app) => (
                          <div key={app.id} className="border rounded-lg p-4">
                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                              <div>
                                <div className="flex items-center space-x-2 mb-2">
                                  <h3 className="font-semibold">{app.data.nickname}</h3>
                                  <Badge variant={
                                    app.status === 'pending' ? 'secondary' :
                                    app.status === 'approved' ? 'default' : 'destructive'
                                  }>
                                    {app.status === 'pending' ? 'Ожидание' :
                                     app.status === 'approved' ? 'Одобрено' : 'Отклонено'}
                                  </Badge>
                                </div>
                                <div className="space-y-1 text-sm">
                                  <p><strong>Логин:</strong> {app.data.login}</p>
                                  <p><strong>VK:</strong> <a href={app.data.vk_link} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">Ссылка</a></p>
                                  <p><strong>Канал:</strong> <a href={app.data.channel_link} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">Ссылка</a></p>
                                  <p><strong>Дата подачи:</strong> {new Date(app.created_at).toLocaleString('ru-RU')}</p>
                                </div>
                              </div>
                              <div className="flex flex-col justify-center space-y-2">
                                {app.status === 'pending' && (
                                  <>
                                    <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-2">
                                      <Button 
                                        size="sm" 
                                        onClick={() => handleApplicationAction(app.id, 'approve', 0)}
                                        className="flex-1"
                                      >
                                        Одобрить (Бесплатное)
                                      </Button>
                                      <Button 
                                        size="sm" 
                                        onClick={() => handleApplicationAction(app.id, 'approve', 1)}
                                        className="flex-1"
                                      >
                                        Одобрить (Платное)
                                      </Button>
                                    </div>
                                    <Button 
                                      variant="destructive" 
                                      size="sm" 
                                      onClick={() => handleApplicationAction(app.id, 'reject')}
                                    >
                                      Отклонить
                                    </Button>
                                  </>
                                )}
                                {app.status !== 'pending' && (
                                  <div className="text-sm text-gray-500">
                                    Обработано: {new Date(app.reviewed_at || app.created_at).toLocaleString('ru-RU')}
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                      
                      <PaginationControls
                        currentPageNum={currentPage.applications}
                        totalPages={paginatedApps.totalPages}
                        totalItems={paginatedApps.totalItems}
                        onPageChange={(page) => changePage('applications', page)}
                      />
                    </>
                  );
                })()}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="purchases" className="mt-6">
            <Card>
              <CardHeader>
                <div className="flex flex-col sm:flex-row sm:items-center justify-between space-y-4 sm:space-y-0">
                  <CardTitle>Заявки на покупки</CardTitle>
                  <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-2">
                    {/* Filter by Status */}
                    <Select value={purchaseFilter} onValueChange={setPurchaseFilter}>
                      <SelectTrigger className="w-full sm:w-40">
                        <Filter className="h-4 w-4 mr-2" />
                        <SelectValue placeholder="Статус" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">Все статусы</SelectItem>
                        <SelectItem value="pending">Ожидание</SelectItem>
                        <SelectItem value="approved">Одобрено</SelectItem>
                        <SelectItem value="rejected">Отклонено</SelectItem>
                      </SelectContent>
                    </Select>
                    
                    {/* Sort */}
                    <div className="flex space-x-1">
                      <Select value={sortBy} onValueChange={setSortBy}>
                        <SelectTrigger className="w-full sm:w-32">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="date">Дата</SelectItem>
                          <SelectItem value="name">Пользователь</SelectItem>
                        </SelectContent>
                      </Select>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setSortOrder(sortOrder === 'desc' ? 'asc' : 'desc')}
                      >
                        {sortOrder === 'desc' ? <SortDesc className="h-4 w-4" /> : <SortAsc className="h-4 w-4" />}
                      </Button>
                    </div>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {(() => {
                  const filteredPurchases = filterPurchases(purchases);
                  const paginatedPurchases = paginateData(filteredPurchases, currentPage.purchases);
                  
                  if (paginatedPurchases.totalItems === 0) {
                    return <div className="text-center text-gray-500 py-8">Нет покупок для отображения</div>;
                  }
                  
                  return (
                    <>
                      <div className="space-y-4">
                        {paginatedPurchases.data.map((purchase) => (
                          <div key={purchase.id} className="border rounded-lg p-4">
                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                              <div>
                                <div className="flex items-center space-x-2 mb-2">
                                  <h3 className="font-semibold">{purchase.user_nickname}</h3>
                                  <Badge variant={
                                    purchase.status === 'pending' ? 'secondary' :
                                    purchase.status === 'approved' ? 'default' : 'destructive'
                                  }>
                                    {purchase.status === 'pending' ? 'Ожидание' :
                                     purchase.status === 'approved' ? 'Одобрено' : 'Отклонено'}
                                  </Badge>
                                </div>
                                <div className="space-y-1 text-sm">
                                  <p><strong>Товар:</strong> {purchase.item_name}</p>
                                  <p><strong>Количество:</strong> {purchase.quantity}</p>
                                  <p><strong>Цена:</strong> {purchase.total_price?.toLocaleString()} MC</p>
                                  <p><strong>Дата заказа:</strong> {new Date(purchase.created_at).toLocaleString('ru-RU')}</p>
                                  {purchase.admin_comment && (
                                    <p><strong>Комментарий:</strong> {purchase.admin_comment}</p>
                                  )}
                                </div>
                              </div>
                              <div className="flex flex-col justify-center space-y-2">
                                {purchase.status === 'pending' && (
                                  <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-2">
                                    <Button 
                                      size="sm" 
                                      onClick={() => handlePurchaseAction(purchase.id, 'approve')}
                                      className="flex-1"
                                    >
                                      Одобрить
                                    </Button>
                                    <Button 
                                      variant="destructive" 
                                      size="sm" 
                                      onClick={() => handlePurchaseAction(purchase.id, 'reject')}
                                      className="flex-1"
                                    >
                                      Отклонить
                                    </Button>
                                  </div>
                                )}
                                {purchase.status !== 'pending' && (
                                  <div className="text-sm text-gray-500">
                                    Обработано: {new Date(purchase.reviewed_at || purchase.created_at).toLocaleString('ru-RU')}
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                      
                      <PaginationControls
                        currentPageNum={currentPage.purchases}
                        totalPages={paginatedPurchases.totalPages}
                        totalItems={paginatedPurchases.totalItems}
                        onPageChange={(page) => changePage('purchases', page)}
                      />
                    </>
                  );
                })()}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="reports" className="mt-6">
            <Card>
              <CardHeader>
                <div className="flex flex-col sm:flex-row sm:items-center justify-between space-y-4 sm:space-y-0">
                  <CardTitle>Отчеты</CardTitle>
                  <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-2">
                    {/* Filter by Status */}
                    <Select value={reportFilter} onValueChange={setReportFilter}>
                      <SelectTrigger className="w-full sm:w-40">
                        <Filter className="h-4 w-4 mr-2" />
                        <SelectValue placeholder="Статус" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">Все статусы</SelectItem>
                        <SelectItem value="pending">Ожидание</SelectItem>
                        <SelectItem value="approved">Одобрено</SelectItem>
                        <SelectItem value="rejected">Отклонено</SelectItem>
                      </SelectContent>
                    </Select>
                    
                    {/* Sort */}
                    <div className="flex space-x-1">
                      <Select value={sortBy} onValueChange={setSortBy}>
                        <SelectTrigger className="w-full sm:w-32">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="date">Дата</SelectItem>
                          <SelectItem value="name">Пользователь</SelectItem>
                        </SelectContent>
                      </Select>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setSortOrder(sortOrder === 'desc' ? 'asc' : 'desc')}
                      >
                        {sortOrder === 'desc' ? <SortDesc className="h-4 w-4" /> : <SortAsc className="h-4 w-4" />}
                      </Button>
                    </div>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {(() => {
                  const filteredReports = filterReports(reports);
                  const paginatedReports = paginateData(filteredReports, currentPage.reports);
                  
                  if (paginatedReports.totalItems === 0) {
                    return <div className="text-center text-gray-500 py-8">Нет отчетов для отображения</div>;
                  }
                  
                  return (
                    <>
                      <div className="space-y-4">
                        {paginatedReports.data.map((report) => (
                          <div key={report.id} className="border rounded-lg p-4">
                            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                              <div className="lg:col-span-2">
                                <div className="flex items-center space-x-2 mb-3">
                                  <h3 className="font-semibold">{report.user_nickname}</h3>
                                  <Badge variant={
                                    report.status === 'pending' ? 'secondary' :
                                    report.status === 'approved' ? 'default' : 'destructive'
                                  }>
                                    {report.status === 'pending' ? 'Ожидание' :
                                     report.status === 'approved' ? 'Одобрено' : 'Отклонено'}
                                  </Badge>
                                </div>
                                
                                <div className="space-y-2 mb-4">
                                  <h4 className="font-medium text-sm">Ссылки и просмотры:</h4>
                                  {report.links?.map((link, index) => (
                                    <div key={index} className="flex justify-between items-center bg-gray-50 p-2 rounded text-sm">
                                      <a href={link.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline truncate mr-4">
                                        {link.url}
                                      </a>
                                      <Badge variant="outline">{link.views?.toLocaleString()} просмотров</Badge>
                                    </div>
                                  )) || []}
                                  <div className="text-xs text-gray-500">
                                    Общие просмотры: {(report.links || []).reduce((sum, link) => sum + (link.views || 0), 0).toLocaleString()}
                                  </div>
                                </div>
                                
                                <div className="text-xs text-gray-500">
                                  Дата подачи: {new Date(report.created_at).toLocaleString('ru-RU')}
                                </div>
                                
                                {report.admin_comment && (
                                  <div className="mt-2 p-2 bg-blue-50 rounded text-sm">
                                    <strong>Комментарий админа:</strong> {report.admin_comment}
                                  </div>
                                )}
                              </div>
                              
                              <div className="flex flex-col justify-center space-y-2">
                                {report.status === 'pending' && (
                                  <>
                                    <Input placeholder="Комментарий..." id={`comment-${report.id}`} className="text-sm" />
                                    <div className="flex space-x-2">
                                      <Input 
                                        placeholder="MC (авто)" 
                                        id={`mc-${report.id}`} 
                                        type="number" 
                                        className="flex-1 text-sm"
                                      />
                                      <Button 
                                        size="sm" 
                                        onClick={() => {
                                          const comment = document.getElementById(`comment-${report.id}`)?.value || '';
                                          const customMc = document.getElementById(`mc-${report.id}`)?.value;
                                          handleReportApprove(report.id, customMc ? parseInt(customMc) : null, comment);
                                        }}
                                        className="flex-1"
                                      >
                                        Одобрить
                                      </Button>
                                    </div>
                                    <div className="text-xs text-gray-500 bg-yellow-50 p-2 rounded">
                                      💡 Авто расчет: {Math.max(10, (report.links || []).reduce((sum, link) => sum + (link.views || 0), 0) / 100)} MC
                                    </div>
                                  </>
                                )}
                                {report.status !== 'pending' && (
                                  <div className="text-sm text-gray-500">
                                    Обработано: {new Date(report.reviewed_at || report.created_at).toLocaleString('ru-RU')}
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                      
                      <PaginationControls
                        currentPageNum={currentPage.reports}
                        totalPages={paginatedReports.totalPages}
                        totalItems={paginatedReports.totalItems}
                        onPageChange={(page) => changePage('reports', page)}
                      />
                    </>
                  );
                })()}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="users" className="mt-6">
            <Card>
              <CardHeader>
                <div className="flex flex-col sm:flex-row sm:items-center justify-between space-y-4 sm:space-y-0">
                  <CardTitle>Управление пользователями</CardTitle>
                  <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-2">
                    {/* Search */}
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-500" />
                      <Input
                        placeholder="Поиск по имени/логину..."
                        value={userSearch}
                        onChange={(e) => setUserSearch(e.target.value)}
                        className="pl-10 w-full sm:w-48"
                      />
                    </div>
                    
                    {/* Sort */}
                    <div className="flex space-x-1">
                      <Select value={sortBy} onValueChange={setSortBy}>
                        <SelectTrigger className="w-full sm:w-32">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="date">Дата</SelectItem>
                          <SelectItem value="name">Имя</SelectItem>
                          <SelectItem value="balance">Баланс</SelectItem>
                        </SelectContent>
                      </Select>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setSortOrder(sortOrder === 'desc' ? 'asc' : 'desc')}
                      >
                        {sortOrder === 'desc' ? <SortDesc className="h-4 w-4" /> : <SortAsc className="h-4 w-4" />}
                      </Button>
                    </div>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {(() => {
                  const filteredUsers = filterUsers(users);
                  const paginatedUsers = paginateData(filteredUsers, currentPage.users);
                  
                  if (paginatedUsers.totalItems === 0) {
                    return <div className="text-center text-gray-500 py-8">Пользователи не найдены</div>;
                  }
                  
                  return (
                    <>
                      <div className="space-y-4">
                        {paginatedUsers.data.map((userItem) => (
                          <div key={userItem.id} className={`border rounded-lg p-4 transition-all ${!userItem.is_approved ? 'bg-red-50 border-red-200' : userItem.warnings >= 2 ? 'bg-yellow-50 border-yellow-200' : 'bg-white hover:shadow-md'}`}>
                            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                              <div>
                                <div className="flex items-center space-x-2 mb-3">
                                  <h3 className="font-semibold">{userItem.nickname}</h3>
                                  {!userItem.is_approved && <Badge variant="destructive">Заблокирован</Badge>}
                                  {userItem.warnings >= 2 && userItem.is_approved && <Badge variant="secondary">⚠️ Опасная зона</Badge>}
                                  {userItem.admin_level >= 1 && <Badge variant="outline">Админ</Badge>}
                                </div>
                                <div className="space-y-1 text-sm">
                                  <p><strong>Логин:</strong> {userItem.login}</p>
                                  <div className="flex items-center space-x-2">
                                    <Coins className="h-4 w-4 text-yellow-600" />
                                    <span><strong>Баланс:</strong> {userItem.balance?.toLocaleString() || 0} MC</span>
                                  </div>
                                  <div className="flex items-center space-x-2">
                                    <AlertTriangle className={`h-4 w-4 ${userItem.warnings >= 2 ? 'text-red-600' : 'text-gray-400'}`} />
                                    <span className={userItem.warnings >= 2 ? 'text-red-600 font-semibold' : ''}>
                                      <strong>Предупреждения:</strong> {userItem.warnings || 0}/3
                                    </span>
                                  </div>
                                </div>
                              </div>
                              
                              <div>
                                <div className="space-y-2 text-sm">
                                  <div>
                                    <strong>Статус:</strong> 
                                    <Badge variant={userItem.is_approved ? 'default' : 'destructive'} className="ml-2">
                                      {userItem.is_approved ? 'Одобрен' : 'Заблокирован'}
                                    </Badge>
                                  </div>
                                  <div>
                                    <strong>Тип медиа:</strong>
                                    <Badge variant={userItem.media_type === 1 ? 'default' : 'secondary'} className="ml-2">
                                      {userItem.media_type === 1 ? '💎 Платное' : '🆓 Бесплатное'}
                                    </Badge>
                                  </div>
                                  <div className="flex space-x-1 mt-2">
                                    <Button
                                      variant="outline"
                                      size="sm"
                                      onClick={() => openMediaTypeModal(userItem)}
                                    >
                                      {userItem.media_type === 1 ? <ToggleLeft className="h-4 w-4" /> : <ToggleRight className="h-4 w-4" />}
                                    </Button>
                                  </div>
                                  <div className="text-xs text-gray-500">
                                    Регистрация: {new Date(userItem.created_at || Date.now()).toLocaleString('ru-RU')}
                                  </div>
                                </div>
                              </div>
                              
                              <div className="space-y-2">
                                <div className="grid grid-cols-2 gap-2">
                                  <div>
                                    <Label htmlFor={`balance-${userItem.id}`} className="text-xs">MC</Label>
                                    <Input
                                      id={`balance-${userItem.id}`}
                                      type="number"
                                      placeholder="±MC"
                                      className="text-xs"
                                    />
                                  </div>
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => {
                                      const amount = document.getElementById(`balance-${userItem.id}`)?.value;
                                      if (amount) {
                                        handleUserAction(userItem.id, 'balance', parseInt(amount));
                                        document.getElementById(`balance-${userItem.id}`).value = '';
                                      }
                                    }}
                                  >
                                    Изменить баланс
                                  </Button>
                                </div>
                                
                                <Button
                                  variant="destructive"
                                  size="sm"
                                  className="w-full"
                                  onClick={() => openWarningModal(userItem)}
                                >
                                  ⚠️ Предупреждение
                                </Button>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                      
                      <PaginationControls
                        currentPageNum={currentPage.users}
                        totalPages={paginatedUsers.totalPages}
                        totalItems={paginatedUsers.totalItems}
                        onPageChange={(page) => changePage('users', page)}
                      />
                    </>
                  );
                })()}
              </CardContent>
            </Card>
          </TabsContent>
          
          <TabsContent value="shop" className="mt-6">
            <ShopManagementTab />
          </TabsContent>

          {/* Blacklist Management Tab */}
          <TabsContent value="blacklist" className="mt-6">
            <BlacklistManagementTab />
          </TabsContent>
        </Tabs>
      </div>

      {/* Модальное окно для предупреждения */}
      <Dialog open={showWarningModal} onOpenChange={setShowWarningModal}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>⚠️ Выдать предупреждение</DialogTitle>
            <DialogDescription>
              Пользователь: {warningUser?.nickname}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="warning-reason">Причина предупреждения *</Label>
              <Textarea
                id="warning-reason"
                placeholder="Укажите причину предупреждения..."
                value={warningReason}
                onChange={(e) => setWarningReason(e.target.value)}
                rows={3}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowWarningModal(false)}>
              Отмена
            </Button>
            <Button variant="destructive" onClick={submitWarning}>
              Выдать предупреждение
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Модальное окно для смены типа медиа */}
      <Dialog open={showMediaTypeModal} onOpenChange={setShowMediaTypeModal}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>🔄 Смена типа медиа</DialogTitle>
            <DialogDescription>
              Пользователь: {mediaTypeUser?.nickname}<br/>
              Текущий тип: {mediaTypeUser?.media_type === 1 ? 'Платное' : 'Бесплатное'}<br/>
              Новый тип: {mediaTypeUser?.media_type === 1 ? 'Бесплатное' : 'Платное'}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="media-comment">Комментарий для пользователя</Label>
              <Textarea
                id="media-comment"
                placeholder="Причина смены типа медиа (необязательно)..."
                value={mediaTypeComment}
                onChange={(e) => setMediaTypeComment(e.target.value)}
                rows={3}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowMediaTypeModal(false)}>
              Отмена
            </Button>
            <Button onClick={submitMediaTypeChange}>
              Изменить тип
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

// Shop Management Component for Admin
const ShopManagementTab = () => {
  const { toast } = useToast();
  const [shopItems, setShopItems] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchShopItems();
  }, []);

  const fetchShopItems = async () => {
    try {
      const response = await axios.get(`${API}/admin/shop/items`);
      setShopItems(response.data || []);
    } catch (error) {
      console.error('Failed to fetch shop items:', error);
      toast({
        title: "❌ Ошибка загрузки",
        description: "Не удалось загрузить товары магазина",
        variant: "destructive",
      });
    }
    setLoading(false);
  };

  const updateItemImage = async (itemId, imageUrl) => {
    try {
      await axios.post(`${API}/admin/shop/item/${itemId}/image`, { image_url: imageUrl });
      toast({
        title: "✅ Изображение обновлено",
        description: "Изображение товара успешно обновлено",
      });
      fetchShopItems();
    } catch (error) {
      console.error('Failed to update image:', error);
      toast({
        title: "❌ Ошибка обновления",
        description: error.response?.data?.detail || "Не удалось обновить изображение",
        variant: "destructive",
      });
    }
  };

  if (loading) {
    return <div className="text-center">Загрузка товаров...</div>;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Управление товарами магазина</CardTitle>
        <CardDescription>Добавление и редактирование изображений товаров</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {shopItems.map((item) => (
            <Card key={item.id} className="p-4">
              <div className="space-y-3">
                {/* Current Image */}
                <div className="w-full h-24 rounded-lg bg-gray-100 flex items-center justify-center overflow-hidden">
                  {item.image_url ? (
                    <img 
                      src={item.image_url} 
                      alt={item.name}
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        e.target.style.display = 'none';
                        e.target.nextSibling.style.display = 'flex';
                      }}
                    />
                  ) : null}
                  {!item.image_url && (
                    <div className="text-center">
                      <Image className="h-6 w-6 mx-auto text-gray-400 mb-1" />
                      <span className="text-xs text-gray-500">Нет изображения</span>
                    </div>
                  )}
                </div>
                
                {/* Item Info */}
                <div>
                  <h4 className="font-semibold text-sm">{item.name}</h4>
                  <p className="text-xs text-gray-600 mb-1">{item.category}</p>
                  <p className="text-xs font-semibold text-blue-600">{item.price} MC</p>
                </div>
                
                {/* Image URL Input */}
                <div className="flex space-x-1">
                  <Input
                    id={`image-${item.id}`}
                    placeholder="URL изображения"
                    defaultValue={item.image_url || ''}
                    className="flex-1 text-xs"
                  />
                  <Button 
                    size="sm" 
                    onClick={() => {
                      const imageUrl = document.getElementById(`image-${item.id}`).value;
                      updateItemImage(item.id, imageUrl);
                    }}
                    className="px-2"
                  >
                    <Edit className="h-3 w-3" />
                  </Button>
                </div>
                
                {/* Remove Image Button */}
                {item.image_url && (
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={() => updateItemImage(item.id, '')}
                    className="w-full text-xs"
                  >
                    Убрать изображение
                  </Button>
                )}
              </div>
            </Card>
          ))}
        </div>
        
        {shopItems.length === 0 && (
          <div className="text-center text-gray-500 py-8">
            <div className="text-4xl mb-2">🛒</div>
            <div>Товары не найдены. Инициализируйте магазин сначала.</div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

// Blacklist Management Tab Component
const BlacklistManagementTab = () => {
  const { toast } = useToast();
  const [blacklistData, setBlacklistData] = useState({ ip_blacklist: [], blacklisted_users: [] });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchBlacklist();
  }, []);

  const fetchBlacklist = async () => {
    try {
      const response = await axios.get(`${API}/admin/blacklist`);
      setBlacklistData(response.data);
    } catch (error) {
      console.error('Failed to fetch blacklist:', error);
      toast({
        title: "❌ Ошибка загрузки",
        description: "Не удалось загрузить данные черного списка",
        variant: "destructive",
      });
    }
    setLoading(false);
  };

  const resetUserPreviews = async (userId) => {
    try {
      await axios.post(`${API}/admin/users/${userId}/reset-previews`);
      toast({
        title: "✅ Предпросмотры сброшены",
        description: "Пользователь может снова использовать предпросмотры",
      });
    } catch (error) {
      console.error('Failed to reset previews:', error);
      toast({
        title: "❌ Ошибка сброса",
        description: error.response?.data?.detail || "Не удалось сбросить предпросмотры",
        variant: "destructive",
      });
    }
  };

  const unblacklistUser = async (userId) => {
    try {
      await axios.post(`${API}/admin/users/${userId}/unblacklist`);
      toast({
        title: "✅ Пользователь разблокирован",
        description: "Пользователь был удален из черного списка",
      });
      fetchBlacklist(); // Refresh data
    } catch (error) {
      console.error('Failed to unblacklist user:', error);
      toast({
        title: "❌ Ошибка разблокировки",
        description: error.response?.data?.detail || "Не удалось разблокировать пользователя",
        variant: "destructive",
      });
    }
  };

  if (loading) {
    return <div className="text-center">Загрузка данных черного списка...</div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold mb-4">🚫 Управление черным списком</h2>
        <p className="text-gray-600 mb-6">
          Управление заблокированными пользователями и IP адресами
        </p>
      </div>

      {/* Blacklisted Users */}
      <Card>
        <CardHeader>
          <CardTitle>Заблокированные пользователи</CardTitle>
          <CardDescription>
            Пользователи, заблокированные за превышение лимита предпросмотров
          </CardDescription>
        </CardHeader>
        <CardContent>
          {blacklistData.blacklisted_users.length === 0 ? (
            <div className="text-center text-gray-500 py-8">
              <div className="text-4xl mb-2">✅</div>
              <div>Нет заблокированных пользователей</div>
            </div>
          ) : (
            <div className="space-y-4">
              {blacklistData.blacklisted_users.map((user) => (
                <Card key={user.id} className="p-4">
                  <div className="flex justify-between items-start">
                    <div className="space-y-2 flex-1">
                      <div className="flex items-center gap-2">
                        <Badge variant="destructive">Заблокирован</Badge>
                        <span className="font-semibold">ID: {user.id}</span>
                      </div>
                      
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm">
                        <div>
                          <strong>VK ссылка:</strong> {user.vk_link || 'Удалена'}
                        </div>
                        <div>
                          <strong>Предпросмотры:</strong> {user.previews_used || 0}/{user.previews_limit || 3}
                        </div>
                        <div>
                          <strong>Заблокирован до:</strong>{' '}
                          {new Date(user.blacklist_until).toLocaleDateString('ru-RU', {
                            year: 'numeric',
                            month: 'long',
                            day: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit'
                          })}
                        </div>
                        <div>
                          <strong>IP регистрации:</strong> {user.registration_ip || 'Не сохранен'}
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex gap-2 ml-4">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => resetUserPreviews(user.id)}
                      >
                        Сбросить предпросмотры
                      </Button>
                      <Button
                        variant="destructive"
                        size="sm"
                        onClick={() => unblacklistUser(user.id)}
                      >
                        Разблокировать
                      </Button>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* IP Blacklist */}
      <Card>
        <CardHeader>
          <CardTitle>Заблокированные IP адреса</CardTitle>
          <CardDescription>
            IP адреса, заблокированные в системе регистрации
          </CardDescription>
        </CardHeader>
        <CardContent>
          {blacklistData.ip_blacklist.length === 0 ? (
            <div className="text-center text-gray-500 py-8">
              <div className="text-4xl mb-2">✅</div>
              <div>Нет заблокированных IP адресов</div>
            </div>
          ) : (
            <div className="space-y-4">
              {blacklistData.ip_blacklist.map((ipEntry) => (
                <Card key={ipEntry.id} className="p-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
                    <div>
                      <strong>IP адрес:</strong> {ipEntry.ip_address}
                    </div>
                    <div>
                      <strong>VK ссылка:</strong> {ipEntry.vk_link}
                    </div>
                    <div>
                      <strong>Заблокирован до:</strong>{' '}
                      {new Date(ipEntry.blacklist_until).toLocaleDateString('ru-RU', {
                        year: 'numeric',
                        month: 'short',
                        day: 'numeric'
                      })}
                    </div>
                    <div>
                      <strong>Причина:</strong> {ipEntry.reason}
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-red-600">
              {blacklistData.blacklisted_users.length}
            </div>
            <div className="text-sm text-gray-600">Заблокированных пользователей</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-orange-600">
              {blacklistData.ip_blacklist.length}
            </div>
            <div className="text-sm text-gray-600">Заблокированных IP</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-blue-600">
              {blacklistData.blacklisted_users.filter(u => 
                new Date(u.blacklist_until) > new Date()
              ).length}
            </div>
            <div className="text-sm text-gray-600">Активных блокировок</div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

// Ratings and Leaderboard Page
const RatingsPage = () => {
  const { user, isAuthenticated } = useAuth();
  const { toast } = useToast();
  const [leaderboard, setLeaderboard] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedUser, setSelectedUser] = useState(null);
  const [userRatings, setUserRatings] = useState(null);
  const [ratingForm, setRatingForm] = useState({ rating: 5, comment: '' });
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetchLeaderboard();
  }, []);

  const fetchLeaderboard = async () => {
    try {
      const response = await axios.get(`${API}/leaderboard`);
      setLeaderboard(response.data);
    } catch (error) {
      console.error('Failed to fetch leaderboard:', error);
    }
    setLoading(false);
  };

  const fetchUserRatings = async (userId) => {
    try {
      const response = await axios.get(`${API}/ratings/${userId}`);
      setUserRatings(response.data);
    } catch (error) {
      console.error('Failed to fetch user ratings:', error);
    }
  };

  const submitRating = async () => {
    if (!isAuthenticated) {
      toast({
        title: "❌ Требуется авторизация",
        description: "Войдите в систему для оценки пользователей",
        variant: "destructive",
      });
      return;
    }

    setSubmitting(true);
    try {
      await axios.post(`${API}/ratings`, {
        rated_user_id: selectedUser.user_id,
        rating: ratingForm.rating,
        comment: ratingForm.comment
      });
      
      toast({
        title: "✅ Рейтинг отправлен!",
        description: "Ваша оценка была сохранена",
      });
      
      // Refresh data
      fetchLeaderboard();
      fetchUserRatings(selectedUser.user_id);
      setRatingForm({ rating: 5, comment: '' });
      
    } catch (error) {
      toast({
        title: "❌ Ошибка при отправке рейтинга",
        description: error.response?.data?.detail || error.message,
        variant: "destructive",
      });
    } finally {
      setSubmitting(false);
    }
  };

  const openUserModal = (user) => {
    setSelectedUser(user);
    setUserRatings(null);
    fetchUserRatings(user.user_id);
  };

  const renderStars = (rating) => {
    return Array.from({ length: 5 }, (_, i) => (
      <Star
        key={i}
        className={`h-4 w-4 ${i < rating ? 'fill-yellow-400 text-yellow-400' : 'text-gray-300'}`}
      />
    ));
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 p-4">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold mb-4">🏆 Рейтинг пользователей</h1>
          <p className="text-gray-600">
            Лидерборд лучших пользователей на основе оценок сообщества
          </p>
        </div>

        {loading ? (
          <div className="text-center">Загрузка...</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {leaderboard.map((user, index) => (
              <Card 
                key={user.user_id} 
                className="hover:shadow-lg transition-all duration-300 cursor-pointer relative"
                onClick={() => openUserModal(user)}
              >
                {/* Medal for top 3 */}
                {index < 3 && (
                  <div className="absolute -top-2 -right-2 w-8 h-8 rounded-full flex items-center justify-center text-white font-bold text-sm">
                    {index === 0 && <div className="bg-yellow-500 w-full h-full rounded-full flex items-center justify-center">🥇</div>}
                    {index === 1 && <div className="bg-gray-400 w-full h-full rounded-full flex items-center justify-center">🥈</div>}
                    {index === 2 && <div className="bg-amber-600 w-full h-full rounded-full flex items-center justify-center">🥉</div>}
                  </div>
                )}

                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-2xl font-bold text-gray-400">#{index + 1}</span>
                      {user.nickname}
                    </div>
                    <Badge variant={user.media_type === 1 ? 'default' : 'secondary'}>
                      {user.media_type === 1 ? 'Платное' : 'Бесплатное'}
                    </Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1">
                        {renderStars(Math.round(user.avg_rating))}
                        <span className="ml-2 font-semibold">{user.avg_rating}</span>
                      </div>
                      <span className="text-sm text-gray-600">
                        ({user.total_ratings} оценок)
                      </span>
                    </div>
                    
                    <div>
                      <strong>Канал:</strong>{' '}
                      <a 
                        href={user.channel_link}
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:underline"
                        onClick={(e) => e.stopPropagation()}
                      >
                        Перейти
                      </a>
                    </div>
                    
                    <Button 
                      variant="outline" 
                      size="sm"
                      className="w-full"
                      onClick={(e) => {
                        e.stopPropagation();
                        openUserModal(user);
                      }}
                    >
                      Посмотреть детали
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* User Details Modal */}
        <Dialog open={!!selectedUser} onOpenChange={() => setSelectedUser(null)}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <User className="h-5 w-5" />
                {selectedUser?.nickname}
              </DialogTitle>
              <DialogDescription>
                Детальная информация о пользователе и его рейтингах
              </DialogDescription>
            </DialogHeader>

            {selectedUser && (
              <div className="space-y-6">
                {/* User Stats */}
                <div className="grid grid-cols-2 gap-4">
                  <Card>
                    <CardContent className="p-4 text-center">
                      <div className="flex items-center justify-center gap-1 mb-2">
                        {renderStars(Math.round(selectedUser.avg_rating))}
                      </div>
                      <p className="text-2xl font-bold">{selectedUser.avg_rating}</p>
                      <p className="text-sm text-gray-600">Средний рейтинг</p>
                    </CardContent>
                  </Card>
                  
                  <Card>
                    <CardContent className="p-4 text-center">
                      <p className="text-2xl font-bold">{selectedUser.total_ratings}</p>
                      <p className="text-sm text-gray-600">Всего оценок</p>
                    </CardContent>
                  </Card>
                </div>

                {/* Rating Form */}
                {isAuthenticated && user?.id !== selectedUser.user_id && (
                  <Card>
                    <CardHeader>
                      <CardTitle>Оценить пользователя</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div>
                        <Label>Оценка (1-5 звезд)</Label>
                        <div className="flex items-center gap-2 mt-2">
                          {Array.from({ length: 5 }, (_, i) => (
                            <Star
                              key={i}
                              className={`h-6 w-6 cursor-pointer transition-colors ${
                                i < ratingForm.rating 
                                  ? 'fill-yellow-400 text-yellow-400' 
                                  : 'text-gray-300 hover:text-yellow-200'
                              }`}
                              onClick={() => setRatingForm({ ...ratingForm, rating: i + 1 })}
                            />
                          ))}
                          <span className="ml-2">{ratingForm.rating}/5</span>
                        </div>
                      </div>
                      
                      <div>
                        <Label htmlFor="comment">Комментарий (необязательно)</Label>
                        <Textarea
                          id="comment"
                          value={ratingForm.comment}
                          onChange={(e) => setRatingForm({ ...ratingForm, comment: e.target.value })}
                          placeholder="Поделитесь своим мнением..."
                          className="mt-2"
                        />
                      </div>
                      
                      <Button 
                        onClick={submitRating} 
                        disabled={submitting}
                        className="w-full"
                      >
                        {submitting ? 'Отправка...' : 'Отправить оценку'}
                      </Button>
                    </CardContent>
                  </Card>
                )}

                {/* User Ratings List */}
                {userRatings && (
                  <Card>
                    <CardHeader>
                      <CardTitle>Отзывы пользователей</CardTitle>
                    </CardHeader>
                    <CardContent>
                      {userRatings.ratings.length === 0 ? (
                        <p className="text-gray-600 text-center py-4">Пока нет отзывов</p>
                      ) : (
                        <div className="space-y-4 max-h-64 overflow-y-auto">
                          {userRatings.ratings.map((rating) => (
                            <div key={rating.id} className="border-b pb-3 last:border-b-0">
                              <div className="flex items-center justify-between mb-1">
                                <div className="flex items-center gap-1">
                                  {renderStars(rating.rating)}
                                  <span className="ml-2 font-semibold">{rating.rating}/5</span>
                                </div>
                                <span className="text-sm text-gray-500">
                                  {new Date(rating.created_at).toLocaleDateString('ru-RU')}
                                </span>
                              </div>
                              {rating.comment && (
                                <p className="text-sm text-gray-600 mt-1">{rating.comment}</p>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                )}
              </div>
            )}
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
};

function App() {
  return (
    <AuthProvider>
      <div className="App">
        <BrowserRouter>
          <Navigation />
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/media-list" element={<MediaListPage />} />
            <Route path="/ratings" element={<RatingsPage />} />
            <Route path="/profile" element={<ProfilePage />} />
            <Route path="/shop" element={<ShopPage />} />
            <Route path="/reports" element={<ReportsPage />} />
            <Route path="/admin" element={<AdminPage />} />
          </Routes>
          <Toaster />
        </BrowserRouter>
      </div>
    </AuthProvider>
  );
}

export default App;