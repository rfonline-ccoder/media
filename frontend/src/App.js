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
  Image
} from "lucide-react";

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
    <nav className="bg-gradient-to-r from-blue-900 via-purple-900 to-pink-900 text-white p-4 shadow-2xl">
      <div className="max-w-7xl mx-auto flex justify-between items-center">
        <div className="flex items-center space-x-3">
          <div className="bg-white/20 p-2 rounded-full">
            <Activity className="h-8 w-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold bg-gradient-to-r from-white to-blue-200 bg-clip-text text-transparent">
            SwagMedia
          </h1>
        </div>
        
        <div className="hidden md:flex items-center space-x-8">
          <a href="/" className="hover:text-blue-200 flex items-center space-x-2 transition-all duration-200 hover:scale-105">
            <Home className="h-4 w-4" />
            <span>Главная</span>
          </a>
          
          <a href="/media-list" className="hover:text-blue-200 flex items-center space-x-2 transition-all duration-200 hover:scale-105">
            <Users className="h-4 w-4" />
            <span>Медиа</span>
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

        <div className="flex items-center space-x-4">
          {isAuthenticated && (
            <>
              <div className="bg-white/20 rounded-full px-4 py-2 flex items-center space-x-2">
                <Coins className="h-4 w-4 text-yellow-400" />
                <span className="text-yellow-400 font-semibold">{user?.balance?.toLocaleString() || 0} MC</span>
              </div>

              <Button variant="ghost" size="sm" onClick={logout} className="hover:bg-white/20 transition-all duration-200">
                Выйти
              </Button>
            </>
          )}

          {!isAuthenticated && (
            <div className="flex space-x-3">
              <Button variant="ghost" size="sm" className="hover:bg-white/20 transition-all duration-200" asChild>
                <a href="/login">Войти</a>
              </Button>
              <Button variant="outline" size="sm" className="bg-white/20 border-white/30 hover:bg-white/30 transition-all duration-200" asChild>
                <a href="/register">Регистрация</a>
              </Button>
            </div>
          )}
        </div>
      </div>
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
  const [mediaList, setMediaList] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMediaList();
  }, []);

  const fetchMediaList = async () => {
    try {
      const response = await axios.get(`${API}/media-list`);
      setMediaList(response.data);
    } catch (error) {
      console.error('Failed to fetch media list:', error);
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 p-4">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold text-center mb-8">Список медиа</h1>
        
        {loading ? (
          <div className="text-center">Загрузка...</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {mediaList.map((media, index) => (
              <Card key={index} className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    {media.nickname}
                    <Badge variant={media.media_type === 'Платное' ? 'default' : 'secondary'}>
                      {media.media_type}
                    </Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
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
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
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
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('applications');

  useEffect(() => {
    if (isAuthenticated && !isLoading && user?.admin_level >= 1) {
      fetchAdminData();
    }
  }, [isAuthenticated, isLoading, user]);

  const fetchAdminData = async () => {
    setLoading(true);
    try {
      const [appsRes, purchasesRes, reportsRes, usersRes] = await Promise.all([
        axios.get(`${API}/admin/applications`),
        axios.get(`${API}/admin/purchases`),
        axios.get(`${API}/admin/reports`),
        axios.get(`${API}/admin/users`)
      ]);
      
      setApplications(appsRes.data || []);
      setPurchases(purchasesRes.data || []);
      setReports(reportsRes.data || []);
      setUsers(usersRes.data || []);
      
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

  const handleMediaTypeChange = async (userId, newMediaType, comment = '') => {
    try {
      const userItem = users.find(u => u.id === userId);
      const requestData = {
        user_id: userId,
        new_media_type: newMediaType,
        admin_comment: comment
      };
      
      await axios.post(`${API}/admin/users/${userId}/change-media-type`, requestData);
      const typeNames = {0: "Бесплатное", 1: "Платное"};
      toast({
        title: "🔄 Тип медиа изменен",
        description: `${userItem?.nickname} теперь ${typeNames[newMediaType]} медиа. Пользователь уведомлен.`,
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

  const handleUserAction = async (userId, action, amount = 0) => {
    try {
      const userItem = users.find(u => u.id === userId);
      if (action === 'balance') {
        await axios.post(`${API}/admin/users/${userId}/balance?amount=${amount}`);
        toast({
          title: amount > 0 ? "💰 MC добавлены" : "💸 MC списаны",
          description: `${amount > 0 ? 'Добавлено' : 'Списано'} ${Math.abs(amount)} MC пользователю ${userItem?.nickname}`,
        });
      } else if (action === 'warning') {
        const response = await axios.post(`${API}/admin/users/${userId}/warning`);
        const newWarnings = (userItem?.warnings || 0) + 1;
        
        if (newWarnings >= 3) {
          toast({
            title: "🚨 Пользователь заблокирован!",
            description: `${userItem?.nickname} получил 3-е предупреждение и был автоматически заблокирован`,
            variant: "destructive",
          });
        } else {
          toast({
            title: "⚠️ Предупреждение выдано",
            description: `${userItem?.nickname} получил предупреждение (${newWarnings}/3)`,
          });
        }
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
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="applications">Заявки ({applications.filter(app => app.status === 'pending').length})</TabsTrigger>
            <TabsTrigger value="purchases">Покупки ({purchases.filter(p => p.status === 'pending').length})</TabsTrigger>
            <TabsTrigger value="reports">Отчеты ({reports.filter(r => r.status === 'pending').length})</TabsTrigger>
            <TabsTrigger value="users">Пользователи ({users.length})</TabsTrigger>
            <TabsTrigger value="shop">Магазин</TabsTrigger>
          </TabsList>

          <TabsContent value="applications" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle>Заявки на регистрацию</CardTitle>
              </CardHeader>
              <CardContent>
                {applications.filter(app => app.status === 'pending').length === 0 ? (
                  <div className="text-center text-gray-500">Нет новых заявок</div>
                ) : (
                  applications.filter(app => app.status === 'pending').map((app) => (
                    <div key={app.id} className="border rounded-lg p-4 mb-4">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <h3 className="font-semibold">{app.data.nickname}</h3>
                          <p><strong>Логин:</strong> {app.data.login}</p>
                          <p><strong>VK:</strong> <a href={app.data.vk_link} target="_blank" rel="noopener noreferrer" className="text-blue-600">Ссылка</a></p>
                          <p><strong>Канал:</strong> <a href={app.data.channel_link} target="_blank" rel="noopener noreferrer" className="text-blue-600">Ссылка</a></p>
                        </div>
                        <div className="flex flex-col space-y-2">
                          <div className="flex space-x-2">
                            <Button onClick={() => handleApplicationAction(app.id, 'approve', 0)}>
                              Одобрить (Бесплатное)
                            </Button>
                            <Button onClick={() => handleApplicationAction(app.id, 'approve', 1)}>
                              Одобрить (Платное)
                            </Button>
                          </div>
                          <Button variant="destructive" onClick={() => handleApplicationAction(app.id, 'reject')}>
                            Отклонить
                          </Button>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="purchases" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle>Заявки на покупки</CardTitle>
              </CardHeader>
              <CardContent>
                {purchases.filter(purchase => purchase.status === 'pending').length === 0 ? (
                  <div className="text-center text-gray-500">Нет новых заявок на покупки</div>
                ) : (
                  purchases.filter(purchase => purchase.status === 'pending').map((purchase) => (
                    <div key={purchase.id} className="border rounded-lg p-4 mb-4">
                      <div className="flex justify-between items-center">
                        <div>
                          <h3 className="font-semibold">{purchase.user_nickname}</h3>
                          <p><strong>Товар:</strong> {purchase.item_name}</p>
                          <p><strong>Количество:</strong> {purchase.quantity}</p>
                          <p><strong>Цена:</strong> {purchase.total_price} MC</p>
                        </div>
                        <div className="flex space-x-2">
                          <Button onClick={() => handlePurchaseAction(purchase.id, 'approve')}>
                            Одобрить
                          </Button>
                          <Button variant="destructive" onClick={() => handlePurchaseAction(purchase.id, 'reject')}>
                            Отклонить
                          </Button>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="reports" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle>Отчеты на рассмотрении</CardTitle>
              </CardHeader>
              <CardContent>
                {reports.filter(report => report.status === 'pending').length === 0 ? (
                  <div className="text-center text-gray-500">Нет новых отчетов</div>
                ) : (
                  reports.filter(report => report.status === 'pending').map((report) => (
                    <div key={report.id} className="border rounded-lg p-4 mb-4">
                      <div className="mb-4">
                        <h3 className="font-semibold">{report.user_nickname}</h3>
                        <div className="space-y-1 mt-2">
                          {report.links.map((link, index) => (
                            <div key={index} className="flex justify-between">
                              <a href={link.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                                {link.url}
                              </a>
                              <span>{link.views} просмотров</span>
                            </div>
                          ))}
                        </div>
                      </div>
                      <div className="flex space-x-2 mb-2">
                        <Input placeholder="Комментарий..." id={`comment-${report.id}`} className="flex-1" />
                        <Input 
                          placeholder="MC (авто)" 
                          id={`mc-${report.id}`} 
                          type="number" 
                          className="w-24"
                        />
                        <Button onClick={() => {
                          const comment = document.getElementById(`comment-${report.id}`).value;
                          const customMc = document.getElementById(`mc-${report.id}`).value;
                          handleReportApprove(report.id, customMc ? parseInt(customMc) : null, comment);
                        }}>
                          Одобрить
                        </Button>
                      </div>
                      <div className="text-xs text-gray-500">
                        💡 Оставьте поле MC пустым для автоматического расчета ({Math.max(10, report.links.reduce((sum, link) => sum + (link.views || 0), 0) / 100)} MC)
                      </div>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="users" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle>Управление пользователями</CardTitle>
              </CardHeader>
              <CardContent>
                {users.map((userItem) => (
                  <div key={userItem.id} className={`border rounded-lg p-4 mb-4 ${!userItem.is_approved ? 'bg-red-50 border-red-200' : userItem.warnings >= 2 ? 'bg-yellow-50 border-yellow-200' : 'bg-white'}`}>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div>
                        <h3 className="font-semibold flex items-center space-x-2">
                          <span>{userItem.nickname}</span>
                          {!userItem.is_approved && <Badge variant="destructive">Заблокирован</Badge>}
                          {userItem.warnings >= 2 && userItem.is_approved && <Badge variant="secondary">⚠️ Опасная зона</Badge>}
                        </h3>
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
                      <div>
                        <p><strong>Статус:</strong> 
                          <Badge variant={userItem.is_approved ? 'default' : 'destructive'} className="ml-2">
                            {userItem.is_approved ? 'Одобрен' : 'Заблокирован'}
                          </Badge>
                        </p>
                        <p><strong>Тип:</strong> 
                          <Badge variant={userItem.media_type === 1 ? 'default' : 'secondary'} className="ml-2">
                            {userItem.media_type === 1 ? 'Платное' : 'Бесплатное'}
                          </Badge>
                        </p>
                        <p><strong>Админ:</strong> {userItem.admin_level > 0 ? '✅ Да' : '❌ Нет'}</p>
                      </div>
                      <div className="space-y-2">
                        <div className="flex space-x-2">
                          <Input placeholder="±100" id={`balance-${userItem.id}`} type="number" className="w-20" />
                          <Button size="sm" onClick={() => {
                            const amount = document.getElementById(`balance-${userItem.id}`).value;
                            if (amount) handleUserAction(userItem.id, 'balance', parseInt(amount));
                          }}>
                            +/- MC
                          </Button>
                        </div>
                        
                        {/* Media Type Toggle */}
                        <div className="flex items-center space-x-2">
                          <span className="text-sm text-gray-600">Тип:</span>
                          <Button
                            size="sm"
                            variant={userItem.media_type === 1 ? "default" : "outline"}
                            onClick={() => {
                              const newType = userItem.media_type === 1 ? 0 : 1;
                              const comment = window.prompt(`Смена типа медиа для ${userItem.nickname} на ${newType === 1 ? 'Платное' : 'Бесплатное'}.\nКомментарий (необязательно):`, '');
                              if (comment !== null) {
                                handleMediaTypeChange(userItem.id, newType, comment);
                              }
                            }}
                            className="flex items-center space-x-1"
                          >
                            {userItem.media_type === 1 ? (
                              <>
                                <ToggleRight className="h-4 w-4" />
                                <span>Платное</span>
                              </>
                            ) : (
                              <>
                                <ToggleLeft className="h-4 w-4" />
                                <span>Бесплатное</span>
                              </>
                            )}
                          </Button>
                        </div>
                        
                        {userItem.is_approved && (
                          <Button 
                            variant={userItem.warnings >= 2 ? "destructive" : "outline"}
                            size="sm"
                            onClick={() => handleUserAction(userItem.id, 'warning')}
                            className="w-full"
                          >
                            {userItem.warnings >= 2 ? '🚨 Последнее предупреждение!' : 'Выдать предупреждение'}
                          </Button>
                        )}
                        {!userItem.is_approved && (
                          <div className="text-sm text-red-600 p-2 bg-red-50 rounded">
                            Пользователь заблокирован за превышение лимита предупреждений
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          </TabsContent>
          
          <TabsContent value="shop" className="mt-6">
            <ShopManagementTab />
          </TabsContent>
        </Tabs>
      </div>
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